import requests
import time
import sys

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000/api" # Your FastAPI backend URL

# --- Test Functions ---

def run_test_sequence():
    """Runs the sequence of API tests."""
    chat_id = None
    headers = {"Content-Type": "application/json"}

    try:
        print("--- Starting API Test Sequence ---")

        # 1. Create Chat
        print("\n[1] Testing POST /chats (Create Chat)")
        create_payload = {"name": "API Test Chat"}
        response = requests.post(f"{BASE_URL}/chats", json=create_payload, headers=headers)
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        chat_info = response.json()
        chat_id = chat_info.get('id')
        assert chat_id, "Chat ID not found in response"
        assert chat_info.get('name') == "API Test Chat", "Chat name mismatch"
        print(f"    Chat created successfully. ID: {chat_id}, Name: {chat_info.get('name')}")

        # Give backend a moment if needed
        time.sleep(1)

        # 2. List Chats
        print(f"\n[2] Testing GET /chats (List Chats) - Verifying chat {chat_id} exists")
        response = requests.get(f"{BASE_URL}/chats")
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        chats_list = response.json()
        assert isinstance(chats_list, list), "Response is not a list"
        found = any(chat['id'] == chat_id and chat['name'] == "API Test Chat" for chat in chats_list)
        assert found, f"Newly created chat {chat_id} not found in list"
        print(f"    Chat list retrieved. Found created chat: {found}")

        # 3. Get Chat Details
        print(f"\n[3] Testing GET /chats/{chat_id} (Get Details)")
        response = requests.get(f"{BASE_URL}/chats/{chat_id}")
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        chat_details = response.json()
        assert chat_details['id'] == chat_id
        assert chat_details['name'] == "API Test Chat"
        # Should have system and initial assistant message
        assert len(chat_details.get('messages', [])) >= 2, "Expected at least 2 initial messages"
        assert chat_details['messages'][0]['role'] == 'system'
        assert chat_details['messages'][-1]['role'] == 'assistant'
        print(f"    Chat details retrieved. Found {len(chat_details.get('messages', []))} messages.")
        print(f"    Initial Assistant Message: \"{chat_details['messages'][-1]['content'][:50]}...\"")

        # 4. Send First User Message
        print(f"\n[4] Testing POST /chats/{chat_id}/messages (First User Message)")
        message1_payload = {"content": "Hi there! Let's make a simple calculator app."}
        response = requests.post(f"{BASE_URL}/chats/{chat_id}/messages", json=message1_payload, headers=headers)
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assistant_response1 = response.json()
        assert assistant_response1.get('content'), "Assistant response content is empty"
        print(f"    Assistant Response 1: \"{assistant_response1.get('content', '')[:80]}...\"")
        
        # Give AI time to respond and backend to update
        time.sleep(2) 

        # 5. Send Second User Message (Multi-turn)
        print(f"\n[5] Testing POST /chats/{chat_id}/messages (Second User Message - Multi-turn)")
        message2_payload = {"content": "What are the main features it should have?"}
        response = requests.post(f"{BASE_URL}/chats/{chat_id}/messages", json=message2_payload, headers=headers)
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assistant_response2 = response.json()
        assert assistant_response2.get('content'), "Assistant response 2 content is empty"
        assert assistant_response1.get('content') != assistant_response2.get('content'), "Assistant responses are identical?"
        print(f"    Assistant Response 2: \"{assistant_response2.get('content', '')[:80]}...\"")

        # 6. Rename Chat
        print(f"\n[6] Testing PUT /chats/{chat_id}/rename (Rename Chat)")
        new_name = "Calculator App PRD - Test"
        rename_payload = {"new_name": new_name}
        response = requests.put(f"{BASE_URL}/chats/{chat_id}/rename", json=rename_payload, headers=headers)
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
        print(f"    Rename request sent successfully.")

        time.sleep(1)

        # 7. Verify Rename
        print(f"\n[7] Testing GET /chats/{chat_id} (Verify Rename)")
        response = requests.get(f"{BASE_URL}/chats/{chat_id}")
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        chat_details_renamed = response.json()
        assert chat_details_renamed['name'] == new_name, f"Expected name '{new_name}', got '{chat_details_renamed['name']}'"
        print(f"    Chat name successfully verified as: '{chat_details_renamed['name']}'")

        # 8. Get Compiled PRD
        print(f"\n[8] Testing GET /chats/{chat_id}/prd (Get PRD Markdown)")
        response = requests.get(f"{BASE_URL}/chats/{chat_id}/prd")
        print(f"    Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        prd_content = response.json()
        assert prd_content.get('markdown'), "PRD markdown content is empty"
        # Check if assistant responses are present
        assert assistant_response1.get('content', '###') in prd_content.get('markdown', ''), "First assistant message missing in PRD"
        assert assistant_response2.get('content', '###') in prd_content.get('markdown', ''), "Second assistant message missing in PRD"
        print(f"    PRD Markdown retrieved. Length: {len(prd_content.get('markdown', ''))}")
        # print(f"    PRD Content Sample:\n------\n{prd_content.get('markdown', '')[:200]}...\n------")

        print("\n--- API Test Sequence Completed Successfully ---")

    except AssertionError as e:
        print(f"\n*** TEST FAILED ***: {e}", file=sys.stderr)
        # Optionally add cleanup here if needed (e.g., delete the test chat if endpoint exists)
    except requests.exceptions.ConnectionError as e:
        print(f"\n*** CONNECTION FAILED ***: Could not connect to API at {BASE_URL}. Is the server running?", file=sys.stderr)
    except Exception as e:
        print(f"\n*** UNEXPECTED ERROR ***: {e}", file=sys.stderr)
    finally:
        # Optional: Add cleanup logic here (e.g., delete the chat if you implement that endpoint)
        # if chat_id:
        #     print(f"\nAttempting to delete test chat: {chat_id}")
        #     # delete_response = requests.delete(f"{BASE_URL}/chats/{chat_id}")
        #     # print(f"    Delete Status Code: {delete_response.status_code}")
        pass 

# --- Main Execution ---

if __name__ == "__main__":
    run_test_sequence() 