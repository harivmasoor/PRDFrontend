// Corresponds to Pydantic models in main.py

export interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

export interface ChatInfo {
    id: string;
    name: string;
}

export interface ChatSessionDetail extends ChatInfo {
    messages: ChatMessage[];
    last_response_id?: string | null; // Match backend optional field
}

export interface AssistantResponse {
    role: 'assistant';
    content: string;
}

export interface PrdContent {
    markdown: string;
} 