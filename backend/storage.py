import os
import logging
import json
from azure.data.tables import TableServiceClient, TableClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
TABLE_NAME = os.getenv("PRD_CHAT_TABLE_NAME", "prdchats") # Default to 'prdchats' if not set
PARTITION_KEY = "PRDChatSession" # Use a fixed partition key for simplicity in POC

table_client = None

if not AZURE_STORAGE_CONNECTION_STRING:
    logger.error("Azure Storage Connection String (AZURE_STORAGE_CONNECTION_STRING) is not set.")
else:
    try:
        table_service_client = TableServiceClient.from_connection_string(conn_str=AZURE_STORAGE_CONNECTION_STRING)
        logger.info(f"Table Service Client created for table: {TABLE_NAME}")
        
        # Create table if it doesn't exist
        try:
            table_client = table_service_client.create_table(table_name=TABLE_NAME)
            logger.info(f"Table '{TABLE_NAME}' created successfully.")
        except ResourceExistsError:
            logger.info(f"Table '{TABLE_NAME}' already exists. Getting client.")
            table_client = table_service_client.get_table_client(table_name=TABLE_NAME)
        except Exception as e:
            logger.error(f"Error during table creation/retrieval: {e}")
            table_client = None # Ensure client is None if creation failed

    except Exception as e:
        logger.error(f"Failed to create TableServiceClient: {e}")


def _serialize_messages(messages: list) -> str:
    """Serialize the list of message dictionaries to a JSON string."""
    return json.dumps(messages)

def _deserialize_messages(messages_json: str | None) -> list:
    """Deserialize the JSON string back into a list of dictionaries."""
    if not messages_json:
        return []
    try:
        return json.loads(messages_json)
    except json.JSONDecodeError:
        logger.error("Failed to decode messages JSON from storage.")
        return [] # Return empty list on error

def create_chat_session(chat_id: str, name: str, messages: list, last_response_id: str | None, initial_prd_markdown: str):
    """Creates a new chat session entity in Azure Table Storage."""
    if not table_client:
        logger.error("Table client not initialized. Cannot create chat session.")
        return False

    entity = {
        "PartitionKey": PARTITION_KEY,
        "RowKey": chat_id,
        "Name": name,
        "Messages": _serialize_messages(messages),
        "LastResponseId": last_response_id or "",
        "LatestPrdMarkdown": initial_prd_markdown
    }
    try:
        table_client.create_entity(entity=entity)
        logger.info(f"Chat session created successfully: {chat_id}")
        return True
    except ResourceExistsError:
        logger.warning(f"Chat session with ID {chat_id} already exists.")
        return False # Or handle as needed
    except Exception as e:
        logger.error(f"Failed to create chat session {chat_id}: {e}")
        return False

def get_chat_session(chat_id: str) -> dict | None:
    """Retrieves a chat session entity from Azure Table Storage."""
    if not table_client:
        logger.error("Table client not initialized. Cannot get chat session.")
        return None
    try:
        entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=chat_id)
        # Deserialize messages before returning
        entity['Messages'] = _deserialize_messages(entity.get('Messages'))
        # Handle potentially empty LastResponseId
        if 'LastResponseId' in entity and not entity['LastResponseId']:
             entity['LastResponseId'] = None
        logger.info(f"Retrieved chat session: {chat_id}")
        return entity
    except ResourceNotFoundError:
        logger.warning(f"Chat session not found: {chat_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve chat session {chat_id}: {e}")
        return None

def list_chat_sessions() -> list[dict]:
    """Lists basic info (ID, Name) for all chat sessions."""
    if not table_client:
        logger.error("Table client not initialized. Cannot list chat sessions.")
        return []
    try:
        entities = table_client.list_entities(select=["RowKey", "Name"])
        session_list = [
            {"id": entity["RowKey"], "name": entity.get("Name", "Untitled Chat")}
            for entity in entities
        ]
        logger.info(f"Listed {len(session_list)} chat sessions.")
        return session_list
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {e}")
        return []

def update_chat_session(chat_id: str, messages: list, last_response_id: str | None, latest_prd_markdown: str | None):
    """Updates messages, last ID, and latest PRD for a chat session."""
    if not table_client:
        logger.error("Table client not initialized. Cannot update chat session.")
        return False
    
    entity = {
        "PartitionKey": PARTITION_KEY,
        "RowKey": chat_id,
        "Messages": _serialize_messages(messages),
        "LastResponseId": last_response_id or ""
    }
    # Only update the PRD markdown if a new version was provided
    if latest_prd_markdown is not None:
         entity["LatestPrdMarkdown"] = latest_prd_markdown

    try:
        # Use MERGE to update only provided fields
        table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        logger.info(f"Chat session updated successfully: {chat_id}")
        return True
    except ResourceNotFoundError:
        logger.warning(f"Chat session not found for update: {chat_id}")
        return False
    except Exception as e:
        logger.error(f"Failed to update chat session {chat_id}: {e}")
        return False

def rename_chat_session(chat_id: str, new_name: str):
    """Updates the name of a chat session."""
    if not table_client:
        logger.error("Table client not initialized. Cannot rename chat session.")
        return False
    
    entity = {
        "PartitionKey": PARTITION_KEY,
        "RowKey": chat_id,
        "Name": new_name
    }
    try:
        table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        logger.info(f"Chat session renamed successfully: {chat_id} to '{new_name}'")
        return True
    except ResourceNotFoundError:
        logger.warning(f"Chat session not found for rename: {chat_id}")
        return False
    except Exception as e:
        logger.error(f"Failed to rename chat session {chat_id}: {e}")
        return False

# Optional: Add delete function if needed
def delete_chat_session(chat_id: str) -> bool:
    """Deletes a chat session entity from Azure Table Storage."""
    if not table_client:
        logger.error("Table client not initialized. Cannot delete chat session.")
        return False
    try:
        table_client.delete_entity(partition_key=PARTITION_KEY, row_key=chat_id)
        logger.info(f"Chat session deleted successfully: {chat_id}")
        return True
    except ResourceNotFoundError:
        # It's okay if it's already gone
        logger.warning(f"Chat session not found for deletion (might have been deleted already): {chat_id}")
        return True # Treat as success if not found
    except Exception as e:
        logger.error(f"Failed to delete chat session {chat_id}: {e}")
        return False 