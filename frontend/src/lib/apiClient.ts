import { ChatInfo, ChatSessionDetail, PrdContent } from '@/types/chat';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

// Helper function for handling API requests and errors
async function fetchApi<T>(url: string, options: RequestInit = {}): Promise<T> {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    };
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        });

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch {
                // If response is not JSON or empty
                errorData = { detail: response.statusText || 'Unknown server error' };
            }
            console.error(`API Error (${response.status}): ${url}`, errorData);
            // Include status code in the error message if possible
            const message = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
            throw new Error(`API Error: ${response.status} - ${message}`);
        }

        // Handle 204 No Content specifically
        if (response.status === 204) {
            // Return an empty object or null for 204 responses as there's no body
            // Adjust the return type T accordingly where 204 is expected
            return null as T;
        }
        
        // Ensure response has content before parsing JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json() as T;
        } else {
             // Handle cases where the response might not be JSON but still OK (e.g., unexpected response)
             // This shouldn't happen with our defined API, but good practice
             console.warn(`Received non-JSON response from ${url}, status: ${response.status}`);
             return null as T; // Or handle appropriately
        }

    } catch (error) {
        console.error('Network or fetch error:', error);
        // Re-throw the error so the calling component can handle it (e.g., display to user)
        throw error;
    }
}

// --- API Client Functions ---

export const apiClient = {
    // Create a new chat session
    createChat: async (name?: string): Promise<ChatInfo> => {
        const payload = name ? { name } : {};
        return fetchApi<ChatInfo>(`${API_BASE_URL}/chats`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    },

    // List all chat sessions
    listChats: async (): Promise<ChatInfo[]> => {
        return fetchApi<ChatInfo[]>(`${API_BASE_URL}/chats`);
    },

    // Get details for a specific chat session
    getChatDetails: async (chatId: string): Promise<ChatSessionDetail> => {
        if (!chatId) throw new Error("Chat ID is required to get details.");
        return fetchApi<ChatSessionDetail>(`${API_BASE_URL}/chats/${chatId}`);
    },

    // Rename a chat session
    renameChat: async (chatId: string, newName: string): Promise<void> => {
        if (!chatId) throw new Error("Chat ID is required to rename.");
        // Expecting 204 No Content, fetchApi handles this returning null
        await fetchApi<null>(`${API_BASE_URL}/chats/${chatId}/rename`, {
            method: 'PUT',
            body: JSON.stringify({ new_name: newName }),
        });
    },

    // Send a user message and get the assistant's response
    sendMessage: async (chatId: string, content: string): Promise<{ role: string; content: string }> => {
        if (!chatId) throw new Error("Chat ID is required to send a message.");
        return fetchApi<{ role: string; content: string }>(`${API_BASE_URL}/chats/${chatId}/messages`, {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
    },

    // Get the compiled PRD Markdown for a chat session
    getPrdMarkdown: async (chatId: string): Promise<PrdContent> => {
        if (!chatId) throw new Error("Chat ID is required to get PRD markdown.");
        return fetchApi<PrdContent>(`${API_BASE_URL}/chats/${chatId}/prd`);
    },

    // Delete a chat session
    deleteChat: async (chatId: string): Promise<void> => {
        if (!chatId) throw new Error("Chat ID is required to delete.");
        // Expecting 204 No Content
        await fetchApi<null>(`${API_BASE_URL}/chats/${chatId}`, {
            method: 'DELETE',
        });
    },
};

// Define types used by the API client (can be moved to a separate types file)
// These should match the Pydantic models in the backend
export {}; // Add this line if ChatInfo, etc. are not defined here yet 