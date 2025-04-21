'use client'; // Mark this component as a Client Component

import React, { useState, useEffect, useCallback } from 'react';
import { ChatInfo, ChatMessage } from '@/types/chat';
import { apiClient } from '@/lib/apiClient';
import ChatList from '@/components/ChatList';
import ChatView from '@/components/ChatView';
import PrdView from '@/components/PrdView';
import { Toaster, toast } from 'sonner'; // For displaying notifications

export default function Home() {
    const [chats, setChats] = useState<ChatInfo[]>([]);
    const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
    const [currentChatMessages, setCurrentChatMessages] = useState<ChatMessage[]>([]);
    const [currentPrdMarkdown, setCurrentPrdMarkdown] = useState<string>('');
    const [isLoadingChats, setIsLoadingChats] = useState<boolean>(true);
    const [isLoadingChatDetails, setIsLoadingChatDetails] = useState<boolean>(false);
    const [isSendingMessage, setIsSendingMessage] = useState<boolean>(false);
    const [isCreatingChat, setIsCreatingChat] = useState<boolean>(false);

    // --- Data Fetching Callbacks ---

    const fetchChats = useCallback(async () => {
        setIsLoadingChats(true);
        try {
            const chatList = await apiClient.listChats();
            setChats(chatList);
            // If no chat is selected, and there are chats, select the first one?
            // Or leave it unselected until user clicks
            // if (!selectedChatId && chatList.length > 0) {
            //     setSelectedChatId(chatList[0].id);
            // }
        } catch (error: unknown) {
            console.error('Failed to fetch chats:', error);
            // Type guard
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            toast.error(`Failed to load chats: ${message}`);
        } finally {
            setIsLoadingChats(false);
        }
    }, []); // No dependencies, fetches all chats

    const fetchChatDetails = useCallback(async (chatId: string) => {
        if (!chatId) return;
        setIsLoadingChatDetails(true);
        setCurrentChatMessages([]);
        setCurrentPrdMarkdown('');
        try {
            const details = await apiClient.getChatDetails(chatId);
            const displayMessages = (details.messages || []).filter(
                (msg: ChatMessage) => msg.role !== 'system'
            );
            setCurrentChatMessages(displayMessages);

            // Fetch the latest PRD markdown (content of the last assistant message)
            const prdData = await apiClient.getPrdMarkdown(chatId);
            setCurrentPrdMarkdown(prdData.markdown || ''); // Use fetched markdown directly

        } catch (error: unknown) {
            console.error(`Failed to fetch details for chat ${chatId}:`, error);
            // Type guard
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            toast.error(`Failed to load chat details: ${message}`);
            setSelectedChatId(null); // Deselect if details failed to load
        } finally {
            setIsLoadingChatDetails(false);
        }
    }, []);

    // --- Initial Data Load ---
    useEffect(() => {
        fetchChats();
    }, [fetchChats]);

    // --- Fetch Details When Selection Changes ---
    useEffect(() => {
        if (selectedChatId) {
            fetchChatDetails(selectedChatId);
        } else {
            // Clear views if no chat is selected
            setCurrentChatMessages([]);
            setCurrentPrdMarkdown('');
        }
    }, [selectedChatId, fetchChatDetails]);

    // --- Event Handlers ---

    const handleSelectChat = (chatId: string) => {
        if (chatId === selectedChatId) return; // Avoid re-selecting the same chat
        setSelectedChatId(chatId);
    };

    const handleCreateChat = async () => {
        if (isCreatingChat) return; // Prevent double clicks
        setIsCreatingChat(true); // <-- Set loading true
        try {
            // Optionally prompt for name or use default from backend
            const newChat = await apiClient.createChat(); // Uses default name
            toast.success(`Chat "${newChat.name}" created!`);
            setChats(prevChats => [newChat, ...prevChats]); // Add to top of list
            setSelectedChatId(newChat.id); // Select the new chat immediately
        } catch (error: unknown) {
            console.error('Failed to create chat:', error);
            // Type guard
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            toast.error(`Failed to create chat: ${message}`);
        } finally {
            setIsCreatingChat(false); // <-- Set loading false regardless of outcome
        }
    };

    const handleRenameChat = async (chatId: string, newName: string) => {
        if (!newName.trim()) {
            toast.warning("Chat name cannot be empty.");
            return;
        }
        try {
            await apiClient.renameChat(chatId, newName);
            toast.success("Chat renamed successfully!");
            // Update the name in the local state
            setChats(prevChats =>
                prevChats.map(chat =>
                    chat.id === chatId ? { ...chat, name: newName } : chat
                )
            );
        } catch (error: unknown) {
            console.error(`Failed to rename chat ${chatId}:`, error);
            // Type guard
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            toast.error(`Failed to rename chat: ${message}`);
        }
    };

    const handleDeleteChat = async (chatId: string, chatName: string) => {
        // Simple confirmation
        if (!window.confirm(`Are you sure you want to delete the chat "${chatName}"?`)) {
            return;
        }

        try {
            await apiClient.deleteChat(chatId);
            toast.success(`Chat "${chatName}" deleted.`);
            // Remove from local state
            setChats(prevChats => prevChats.filter(chat => chat.id !== chatId));
            // If the deleted chat was selected, deselect it
            if (selectedChatId === chatId) {
                setSelectedChatId(null);
            }
        } catch (error: unknown) {
            console.error(`Failed to delete chat ${chatId}:`, error);
            // Type guard
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            toast.error(`Failed to delete chat: ${message}`);
        }
    };

    const handleSendMessage = async (content: string) => {
        if (!selectedChatId || isSendingMessage) return;

        setIsSendingMessage(true);
        const userMessage: ChatMessage = { role: 'user', content };
        // Optimistically update chat view only
        setCurrentChatMessages(prev => [...prev, userMessage]);

        // Store selectedChatId in a variable to avoid potential state update issues in async calls
        const currentChatId = selectedChatId;

        try {
            // 1. Send message and get CONVERSATIONAL response
            const assistantConversationalResponse = await apiClient.sendMessage(currentChatId, content);
            const assistantMessage: ChatMessage = { role: 'assistant', content: assistantConversationalResponse.content };

            // Update chat messages state with the conversational response
            setCurrentChatMessages(prev => [...prev, assistantMessage]);

            // 2. Fetch the UPDATED PRD markdown SEPARATELY
            try {
                 const prdData = await apiClient.getPrdMarkdown(currentChatId);
                 setCurrentPrdMarkdown(prdData.markdown || ''); // Update PRD preview
            } catch (prdError: unknown) {
                 console.error('Failed to fetch updated PRD markdown:', prdError);
                 // Type guard
                 const message = prdError instanceof Error ? prdError.message : 'An unknown error occurred';
                 toast.error(`Failed to update PRD preview: ${message}`);
                 // Keep the previous PRD markdown displayed if fetch fails
            }

        } catch (error: unknown) {
            console.error('Failed to send message or get response:', error);
            // Type guard
            const message = error instanceof Error ? error.message : 'An unknown error occurred';
            toast.error(`Failed to send message: ${message}`);
            // Rollback optimistic update on error
            setCurrentChatMessages(prev => prev.slice(0, -1));
             // Do NOT try to fetch PRD if sending failed
        } finally {
            setIsSendingMessage(false);
        }
    };

    // --- Rendering ---

    return (
        <main className="flex h-screen w-screen bg-dark-900 text-gray-100">
            <Toaster richColors position="top-center" theme="dark" />
            {/* Left Sidebar: Chat List (Fixed Width) */}
            <div className="w-64 flex-shrink-0 h-full border-r border-dark-700 flex flex-col bg-dark-800">
                <ChatList
                    chats={chats}
                    selectedChatId={selectedChatId}
                    onSelectChat={handleSelectChat}
                    onCreateChat={handleCreateChat}
                    onRenameChat={handleRenameChat}
                    onDeleteChat={handleDeleteChat}
                    isLoading={isLoadingChats}
                    isCreatingChat={isCreatingChat}
                />
            </div>

            {/* Center Area: Chat View (Flexible Width) */}
            <div className="flex-1 h-full flex flex-col border-r border-dark-700 bg-dark-900">
                {selectedChatId ? (
                    <ChatView 
                        messages={currentChatMessages}
                        onSendMessage={handleSendMessage}
                        isLoading={isLoadingChatDetails}
                        isSending={isSendingMessage}
                    /> 
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-500">
                        <p>Select a chat to view the conversation.</p>
                    </div>
                )}
            </div>

            {/* Right Area: PRD View (Flexible Width) */}
            <div className="flex-1 h-full overflow-y-auto p-4 bg-dark-800">
                 {selectedChatId ? (
                    <PrdView 
                        markdown={currentPrdMarkdown}
                        isLoading={isLoadingChatDetails} 
                    />
                 ) : (
                     <div className="flex items-center justify-center h-full text-gray-500">
                         <p>Select or create a chat to view the PRD.</p>
                     </div>
                 )}
            </div>
        </main>
    );
}
