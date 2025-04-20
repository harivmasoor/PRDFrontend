import os
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# Use a specific API version compatible with the Responses API
# Check the documentation for the latest supported version
AZURE_OPENAI_API_VERSION = "2025-03-01-preview" 
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") # Your model deployment name (e.g., gpt-4o)

if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME]):
    logger.error("Missing one or more Azure OpenAI environment variables (ENDPOINT, API_KEY, DEPLOYMENT_NAME)")
    # In a real app, you might raise an exception or handle this more gracefully
    # For now, we allow it to proceed but client creation will likely fail
    azure_client = None
else:
    try:
        azure_client = AzureOpenAI(
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        )
        logger.info("Azure OpenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI client: {e}")
        azure_client = None

# --- Base PRD Template ---
# This is the structure the AI will be working with.
PRD_TEMPLATE = """# Product Requirements Document: {product_name}

_[Version: 0.1 | Date: {date} | Responsible Manager: {manager_name}]_

---

## Introduction

*   **Background Information / Context:** {introduction_background}
*   **Problem Definition / User Needs:** {introduction_problem}

## Objectives

*   **Vision:** {objectives_vision}
*   **Goals:**
{objectives_goals}
*   **Product Positioning:** {objectives_positioning}
*   **Success Metrics:** {objectives_metrics}

## Stakeholders

*   **Users:** {stakeholders_users}
*   **Purchasers:** {stakeholders_purchasers}
*   **Manufacturing:** {stakeholders_manufacturing}
*   **Customer Service:** {stakeholders_cs}
*   **Marketing & Sales:** {stakeholders_marketing}
*   **External Partners:** {stakeholders_partners}
*   **Regulatory Instances:** {stakeholders_regulatory}
*   _(Add others as needed)_

## Use Cases / User Stories

{use_cases_stories}

## Aspects & Requirements

*   **Hardware:** (P{hardware_priority})
{hardware_reqs}
*   **Software:** (P{software_priority})
{software_reqs}
*   **Design (Aesthetics/Form):** (P{design_priority})
{design_reqs}
*   **User Experience (UX) / Interactivity:** (P{ux_priority})
{ux_reqs}
*   **Customization:** (P{customization_priority})
{customization_reqs}
*   **Manufacturing:** (P{manufacturing_priority})
{manufacturing_reqs}
*   **Regulations / Compliance:** (P{compliance_priority})
{compliance_reqs}
*   _(Add other relevant aspect categories)_

## Open Questions / Future Work

{open_questions}

## Milestones

*   **Concept Presentation:** {milestone_concept}
*   **Design Freeze:** {milestone_freeze}
*   **Manufacturing Start:** {milestone_mfg}
*   **Release Date:** {milestone_release}

---
"""

# Initial values for the template placeholders
INITIAL_PLACEHOLDERS = {
    "product_name": "[Product Name]",
    "date": "[Date]",
    "manager_name": "[Manager Name]",
    "introduction_background": "[Provide context, market landscape, etc.]",
    "introduction_problem": "[Clearly state the problem this product solves or the need it fulfills]",
    "objectives_vision": "[Describe the high-level, long-term vision for this product]",
    "objectives_goals": "    *   Goal 1: (P_) [Describe SMART Goal]",
    "objectives_positioning": "[How does this product fit in the market compared to competitors? Target segment?]",
    "objectives_metrics": "[KPIs to measure success, e.g., adoption rate, user satisfaction, revenue]",
    "stakeholders_users": "[Describe primary and secondary user personas]",
    "stakeholders_purchasers": "[If different from users, e.g., IT admins]",
    "stakeholders_manufacturing": "[Relevant production teams/constraints]",
    "stakeholders_cs": "[Support team requirements]",
    "stakeholders_marketing": "[Go-to-market considerations]",
    "stakeholders_partners": "[Any collaborators?]",
    "stakeholders_regulatory": "[Compliance bodies?]",
    "use_cases_stories": "*   **Use Case 1: [Name]**\n    *   *Actor:* [User type]\n    *   *Goal:* [Objective]\n    *   *Steps:* [Sequence]\n*   **User Story 1:** As a [user type], I want to [action] so that [benefit]. (P_)",
    "hardware_priority": "_", "hardware_reqs": "    *   Requirement 1.1:",
    "software_priority": "_", "software_reqs": "    *   Requirement 2.1:",
    "design_priority": "_", "design_reqs": "    *   Requirement 3.1:",
    "ux_priority": "_", "ux_reqs": "    *   Requirement 4.1:",
    "customization_priority": "_", "customization_reqs": "    *   Requirement 5.1:",
    "manufacturing_priority": "_", "manufacturing_reqs": "    *   Requirement 6.1:",
    "compliance_priority": "_", "compliance_reqs": "    *   Requirement 7.1:",
    "open_questions": "*   [List questions needing answers before finalization]",
    "milestone_concept": "[Target Date]", "milestone_freeze": "[Target Date]",
    "milestone_mfg": "[Target Date]", "milestone_release": "[Target Date]",
}

# Generate the initial blank PRD using the template and placeholders
INITIAL_PRD_MARKDOWN = PRD_TEMPLATE.format(**INITIAL_PLACEHOLDERS)

# --- Define Delimiter ---
DELIMITER = "\n---\nPRD_MARKDOWN_START\n---\n"

# --- Define Initial Conversational Message BEFORE System Prompt uses it ---
INITIAL_ASSISTANT_MESSAGE_CONVO = "Okay, I'm ready to help you build your PRD for 8090 Solutions. Here is the initial template. To start, could you please tell me about the product idea? What core problem does it solve, and who is the primary target audience?"

# --- System Prompt ---
# This prompt now instructs the AI to rewrite the *entire* document.
SYSTEM_PROMPT_PRD = f"""You are an expert Product Manager AI assistant for 8090 Solutions. Your task is to collaboratively build a Product Requirements Document (PRD) with the user.

**Core Instruction:**
Your response MUST contain two parts separated by a specific delimiter:
1.  A **conversational message** to the user (e.g., acknowledging input, asking the next relevant question based on the PRD template).
2.  The delimiter: `\\n---\\nPRD_MARKDOWN_START\\n---\\n`
3.  The **COMPLETE and UPDATED PRD document** in well-formatted Markdown, incorporating all information gathered so far.

**PRD Template Structure (Use this format for the second part):**
```markdown
{PRD_TEMPLATE}
```

**Initial State:**
The initial PRD looks like this:
```markdown
{INITIAL_PRD_MARKDOWN}
```

**Interaction Flow:**
1.  For the **very first turn**, your conversational message should be: "{INITIAL_ASSISTANT_MESSAGE_CONVO}" followed by the delimiter and the initial PRD markdown.
2.  For **all subsequent turns**:
    *   Analyze the user's latest message and the conversation history (implicitly provided by the API context).
    *   Determine the next piece of information needed based on the PRD structure.
    *   Formulate a concise conversational question or comment for the user.
    *   Rewrite the *entire* PRD markdown document, incorporating the latest user information into the correct placeholders or sections.
    *   Output the conversational part, then the delimiter, then the full updated PRD markdown.

**Example Turn:**

*User Message:* "The product name is PodYar."

*Your Output:*
Okay, I've updated the product name to PodYar. What is the high-level vision for this product?
---
PRD_MARKDOWN_START
---
# Product Requirements Document: PodYar

_[Version: 0.1 | Date: [Date] | Responsible Manager: [Manager Name]]_

---
## Introduction
*   **Background Information / Context:** [Provide context, market landscape, etc.]
# ... (rest of the document updated/unchanged) ...
---

Remember the delimiter and always provide both parts.

Start the conversation. Remember to always output the full PRD markdown.
"""

# --- Initial Assistant Full Output (Used by main.py) ---
# The first *full output* expected from the AI after the system prompt call
INITIAL_ASSISTANT_FULL_OUTPUT = f"{INITIAL_ASSISTANT_MESSAGE_CONVO}\n{DELIMITER}\n{INITIAL_PRD_MARKDOWN}"

# --- PRD Generation Logic ---

def get_prd_update(input_data: list, previous_response_id: str | None = None) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Sends the input to the Azure OpenAI Responses API and gets the next response.
    Parses the response into conversational text and PRD markdown.

    Returns:
        A tuple containing:
        - Conversational response part (str or None if error/not found).
        - Full PRD markdown part (str or None if error/not found).
        - The ID of the new response (str or None if error).
        - An error message (str or None if success).
    """
    if not azure_client:
        error_msg = "Azure OpenAI client is not initialized."
        logger.error(error_msg)
        return None, None, None, error_msg

    if not AZURE_OPENAI_DEPLOYMENT_NAME:
        error_msg = "Azure OpenAI deployment name is not configured."
        logger.error(error_msg)
        return None, None, None, error_msg

    try:
        logger.info(f"Sending request to Responses API. Previous ID: {previous_response_id}. Input: {input_data}")
        response = azure_client.responses.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            input=input_data,
            previous_response_id=previous_response_id,
        )
        logger.info(f"Received response from API. Response ID: {response.id}, Status: {response.status}")

        if response.status == "completed" and response.output:
            raw_assistant_content = None
            for output_item in response.output:
                if output_item.type == "message" and output_item.role == "assistant" and output_item.content:
                    for content_item in output_item.content:
                        if content_item.type == "output_text":
                            raw_assistant_content = content_item.text
                            break
                    if raw_assistant_content:
                        break

            if raw_assistant_content:
                logger.info(f"Extracted raw assistant content. Length: {len(raw_assistant_content)}")
                if DELIMITER in raw_assistant_content:
                    parts = raw_assistant_content.split(DELIMITER, 1)
                    conversational_part = parts[0].strip()
                    prd_markdown_part = parts[1].strip()
                    logger.info("Successfully parsed response into conversation and PRD parts.")
                    return conversational_part, prd_markdown_part, response.id, None
                else:
                    logger.warning(f"Delimiter '{DELIMITER}' not found in response. Treating entire output as conversational.")
                    return raw_assistant_content.strip(), None, response.id, None
            else:
                error_msg = "Response completed but no assistant text output found."
                logger.warning(error_msg)
                return None, None, response.id, error_msg

        elif response.error:
            error_msg = f"Responses API error: {response.error.message}"
            logger.error(error_msg)
            return None, None, response.id, error_msg
        else:
            error_msg = f"Response status not 'completed' or no output received. Status: {response.status}"
            logger.warning(error_msg)
            return None, None, response.id, error_msg

    except Exception as e:
        error_msg = f"Error calling Azure OpenAI Responses API: {e}"
        logger.exception(error_msg)
        return None, None, None, error_msg
