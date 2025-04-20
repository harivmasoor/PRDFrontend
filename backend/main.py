import os
import uuid
import logging
from fastapi import FastAPI, HTTPException, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

# Import helpers from other modules
from prd import (
    get_prd_update, SYSTEM_PROMPT_PRD,
    INITIAL_ASSISTANT_MESSAGE_CONVO, # Use this for the first display message
    INITIAL_PRD_MARKDOWN, # Use this for initial storage
    # INITIAL_ASSISTANT_PRD_OUTPUT is no longer directly stored
)
import storage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models ---

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (e.g., 'system', 'user', 'assistant')")
    content: str = Field(..., description="Content of the message")

class NewChatRequest(BaseModel):
    name: Optional[str] = Field(None, description="Optional initial name for the chat session")

class UserMessageRequest(BaseModel):
    content: str = Field(..., description="The user's message content")

class RenameRequest(BaseModel):
    new_name: str = Field(..., description="The new name for the chat session")

class ChatInfo(BaseModel):
    id: str = Field(..., description="Unique ID of the chat session")
    name: str = Field(..., description="Name of the chat session")

class ChatSessionDetail(ChatInfo):
    messages: List[ChatMessage] = Field(..., description="List of messages in the chat session")
    last_response_id: Optional[str] = Field(None, description="The ID of the last response from the Azure API for chaining")

class AssistantResponse(BaseModel):
    role: str = "assistant"
    content: str

class PrdContent(BaseModel):
    markdown: str = Field(..., description="The compiled PRD content in Markdown format")


# --- FastAPI App Initialization ---

app = FastAPI(
    title="PRD Generator API",
    description="API for managing PRD chat sessions using Azure OpenAI Responses API and Azure Table Storage",
    version="1.0.0"
)

# --- CORS Middleware --- 
# Allow all origins for simplicity in POC, adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify frontend origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.post("/api/chats", response_model=ChatInfo, status_code=201)
def create_new_chat(request_body: NewChatRequest = Body(None)):
    """
    Creates a new chat session (PRD).
    Makes the initial call to the Responses API with the system prompt
    to establish the context. Stores initial conversational message
    and initial PRD markdown separately.
    """
    chat_id = str(uuid.uuid4())
    chat_name = request_body.name if request_body and request_body.name else f"PRD Chat - {chat_id[:8]}"
    logger.info(f"Attempting to create new chat: {chat_id} named '{chat_name}'")

    initial_api_input = [{"type": "message", "role": "system", "content": SYSTEM_PROMPT_PRD}]

    # Make the initial call to establish the response chain ID.
    # We expect the AI's first response (based on the revised prompt)
    # to contain both the conversational greeting AND the initial PRD.
    _, _, initial_response_id, error = get_prd_update(
        input_data=initial_api_input,
        previous_response_id=None
    )

    if error or not initial_response_id:
        logger.error(f"Failed to establish initial context chain with API for chat {chat_id}: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize chat context with AI: {error}")

    # Store the system prompt and the initial *conversational* message.
    initial_messages_stored = [
        {"role": "system", "content": SYSTEM_PROMPT_PRD},
        {"role": "assistant", "content": INITIAL_ASSISTANT_MESSAGE_CONVO} # Store only the greeting part
    ]

    # Save to storage, including the initial PRD markdown state
    success = storage.create_chat_session(
        chat_id=chat_id,
        name=chat_name,
        messages=initial_messages_stored,
        last_response_id=initial_response_id,
        initial_prd_markdown=INITIAL_PRD_MARKDOWN # Store the initial template
    )
    if not success:
        logger.error(f"Failed to save new chat session {chat_id} to storage.")
        raise HTTPException(status_code=500, detail="Failed to save chat session to storage")

    logger.info(f"Successfully created and saved chat: {chat_id}, initial response ID: {initial_response_id}")
    return ChatInfo(id=chat_id, name=chat_name)

@app.get("/api/chats", response_model=List[ChatInfo])
def get_all_chats():
    """Lists all available chat sessions (ID and Name)."""
    chats = storage.list_chat_sessions()
    return chats

@app.get("/api/chats/{chat_id}", response_model=ChatSessionDetail)
def get_chat_details(chat_id: str = Path(..., description="The unique ID of the chat session")):
    """Retrieves the full details (messages, name) for a specific chat session."""
    logger.info(f"Attempting to retrieve chat details for: {chat_id}")
    session_data = storage.get_chat_session(chat_id)
    if not session_data:
        logger.warning(f"Chat not found: {chat_id}")
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Map the raw storage data (dict) to the Pydantic model
    return ChatSessionDetail(
        id=session_data['RowKey'], 
        name=session_data.get('Name', 'Untitled Chat'),
        messages=[ChatMessage(**msg) for msg in session_data.get('Messages', [])],
        last_response_id=session_data.get('LastResponseId')
    )

@app.put("/api/chats/{chat_id}/rename", status_code=204)
def rename_chat(
    chat_id: str = Path(..., description="The unique ID of the chat session to rename"),
    request_body: RenameRequest = Body(...)
):
    """Renames a specific chat session."""
    logger.info(f"Attempting to rename chat {chat_id} to '{request_body.new_name}'")
    success = storage.rename_chat_session(chat_id, request_body.new_name)
    if not success:
        # Could be not found or other storage error
        logger.warning(f"Failed to rename chat {chat_id}. It might not exist or storage failed.")
        # Check if it exists first to give a more specific error
        if storage.get_chat_session(chat_id) is None:
             raise HTTPException(status_code=404, detail="Chat session not found")
        else:
             raise HTTPException(status_code=500, detail="Failed to rename chat session in storage")
    logger.info(f"Successfully renamed chat {chat_id}")
    return # Return 204 No Content on success

@app.post("/api/chats/{chat_id}/messages", response_model=AssistantResponse)
def post_user_message(
    chat_id: str = Path(..., description="The unique ID of the chat session"),
    user_message: UserMessageRequest = Body(...)
):
    """
    Sends user message, gets AI response (conversational + PRD),
    stores conversational part in messages, updates latest PRD in session,
    and returns only the conversational part.
    """
    logger.info(f"Received message for chat {chat_id}")
    session_data = storage.get_chat_session(chat_id)
    if not session_data:
        logger.warning(f"Chat not found when posting message: {chat_id}")
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = session_data.get('Messages', [])
    last_response_id = session_data.get('LastResponseId')

    # Append the new user message locally first
    user_message_dict = {"role": "user", "content": user_message.content}
    messages.append(user_message_dict)

    # Prepare API input (just the user message)
    api_input = [{"type": "message", "role": "user", "content": user_message.content}]

    logger.info(f"Sending message to OpenAI for chat {chat_id}. Last Response ID: {last_response_id}")
    # Get both parts from the AI response
    conversational_part, prd_markdown_part, new_response_id, error = get_prd_update(
        input_data=api_input,
        previous_response_id=last_response_id
    )

    if error or conversational_part is None: # Check if conversational part exists
        logger.error(f"Failed to get AI response for chat {chat_id}: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {error or 'No conversational content'}")

    # Append only the conversational part to the message history
    assistant_message_dict = {"role": "assistant", "content": conversational_part}
    messages.append(assistant_message_dict)

    # Update the session in storage with new messages, new response ID,
    # and the latest full PRD markdown.
    logger.info(f"Updating chat session {chat_id} in storage. New Response ID: {new_response_id}")
    success = storage.update_chat_session(
        chat_id=chat_id,
        messages=messages,
        last_response_id=new_response_id,
        latest_prd_markdown=prd_markdown_part # Pass the PRD part here
    )

    if not success:
        logger.error(f"Failed to update chat session {chat_id} in storage after getting AI response.")
        raise HTTPException(status_code=500, detail="Failed to save updated chat session to storage")

    logger.info(f"Successfully processed message and updated chat {chat_id}")
    # Return ONLY the conversational part to the frontend
    return AssistantResponse(content=conversational_part)

@app.get("/api/chats/{chat_id}/prd", response_model=PrdContent)
def get_prd_markdown(
    chat_id: str = Path(..., description="The unique ID of the chat session")
):
    """
    Retrieves the latest full PRD markdown stored for the chat session.
    """
    logger.info(f"Retrieving PRD for chat {chat_id}")
    session_data = storage.get_chat_session(chat_id)
    if not session_data:
        logger.warning(f"Chat not found when retrieving PRD: {chat_id}")
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Retrieve the dedicated field
    latest_markdown = session_data.get('LatestPrdMarkdown', '') # Default to empty string if field missing

    # No need to strip preamble here, as storage should contain clean PRD
    if not latest_markdown:
        # If it's somehow empty/missing after creation, return the initial template as fallback
        logger.warning(f"LatestPrdMarkdown field empty/missing for chat {chat_id}, returning initial template.")
        latest_markdown = INITIAL_PRD_MARKDOWN

    logger.info(f"Successfully retrieved PRD for chat {chat_id}. Length: {len(latest_markdown)}")
    return PrdContent(markdown=latest_markdown)

@app.delete("/api/chats/{chat_id}", status_code=204)
def delete_chat(
    chat_id: str = Path(..., description="The unique ID of the chat session to delete")
):
    """Deletes a specific chat session."""
    logger.info(f"Attempting to delete chat {chat_id}")
    success = storage.delete_chat_session(chat_id)
    if not success:
        # Don't raise 404 if storage.delete_chat_session returns True for not found
        # Only raise 500 if the deletion actually failed due to an unexpected error
        logger.error(f"Failed to delete chat session {chat_id} due to storage error.")
        raise HTTPException(status_code=500, detail="Failed to delete chat session in storage")
    logger.info(f"Successfully deleted chat {chat_id} (or it was already gone).")
    return # Return 204 No Content on success

# --- Uvicorn Runner (for local development) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000)) # Use PORT env var if available (common in deployment)
    logger.info(f"Starting Uvicorn server on port {port}")
    # Check if storage and OpenAI clients are initialized before starting
    if not storage.table_client:
        logger.critical("Azure Table Storage client failed to initialize. Cannot start server. Check connection string and table name.")
    # You might want a similar check for the azure_client in prd.py if it's critical
    # elif not prd.azure_client: 
    #     logger.critical("Azure OpenAI client failed to initialize. Cannot start server. Check credentials and endpoint.")
    else:
         uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
