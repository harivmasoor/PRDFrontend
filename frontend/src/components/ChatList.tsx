'use client';

import React, { useState } from 'react';
import { ChatInfo } from '@/types/chat';
import { PlusCircleIcon, PencilIcon, CheckIcon, XMarkIcon, TrashIcon } from '@heroicons/react/24/outline'; // Using Heroicons
import { toast } from 'sonner';

interface ChatListProps {
    chats: ChatInfo[];
    selectedChatId: string | null;
    onSelectChat: (chatId: string) => void;
    onCreateChat: () => void;
    onRenameChat: (chatId: string, newName: string) => Promise<void>; // Make async to handle potential errors
    onDeleteChat: (chatId: string, chatName: string) => Promise<void>; // Add delete handler prop
    isLoading: boolean;
    isCreatingChat: boolean; // <-- Add new prop
}

export default function ChatList({ 
    chats, 
    selectedChatId, 
    onSelectChat, 
    onCreateChat,
    onRenameChat,
    onDeleteChat, // Destructure the new prop
    isLoading,
    isCreatingChat // <-- Destructure new prop
}: ChatListProps) {
    const [editingChatId, setEditingChatId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState<string>('');

    const handleStartRename = (chat: ChatInfo) => {
        setEditingChatId(chat.id);
        setRenameValue(chat.name);
    };

    const handleCancelRename = () => {
        setEditingChatId(null);
        setRenameValue('');
    };

    const handleConfirmRename = async () => {
        if (!editingChatId || !renameValue.trim()) {
            toast.warning("Chat name cannot be empty.");
            return; // Or handle error appropriately
        }
        try {
            await onRenameChat(editingChatId, renameValue.trim());
            setEditingChatId(null);
            setRenameValue('');
        } catch {
            // Error is already handled and toasted in the parent component (page.tsx)
            // We might still want to keep the input open on error, or close it?
            // Let's close it for now.
            handleCancelRename(); 
        }
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleConfirmRename();
        } else if (event.key === 'Escape') {
            handleCancelRename();
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header with Create Button */}
            <div className="p-4 border-b border-dark-700 flex justify-between items-center flex-shrink-0">
                <h2 className="text-lg font-semibold text-gray-100">PRD Chats</h2>
                <button 
                    onClick={onCreateChat} 
                    className="p-1 text-gray-200 hover:text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Create New Chat"
                    disabled={isCreatingChat}
                >
                    <PlusCircleIcon className="h-6 w-6" />
                </button>
            </div>

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto">
                {isLoading ? (
                    <div className="p-4 text-center text-gray-400">Loading chats...</div>
                ) : chats.length === 0 ? (
                    <div className="p-4 text-center text-gray-400">No chats yet. Create one!</div>
                ) : (
                    <ul>
                        {chats.map((chat) => (
                            <li key={chat.id} >
                                <div className={`
                                    flex items-center justify-between p-3 cursor-pointer 
                                    transition-colors border-l-4 
                                    ${selectedChatId === chat.id 
                                        ? 'bg-dark-700 border-accent' 
                                        : 'border-transparent hover:bg-dark-700/50'}
                                `}>
                                    {editingChatId === chat.id ? (
                                        <input
                                            type="text"
                                            value={renameValue}
                                            onChange={(e) => setRenameValue(e.target.value)}
                                            onKeyDown={handleKeyDown}
                                            onBlur={handleCancelRename}
                                            className="flex-grow bg-dark-900 border border-accent rounded px-2 py-1 text-sm mr-2 text-gray-100"
                                            autoFocus
                                        />
                                    ) : (
                                        <span 
                                           onClick={() => onSelectChat(chat.id)}
                                           className="flex-grow truncate mr-2 text-sm text-gray-100"
                                           title={chat.name}
                                        >
                                            {chat.name}
                                        </span>
                                    )}
                                    
                                    {editingChatId === chat.id ? (
                                        <div className="flex-shrink-0 flex items-center space-x-1">
                                             <button 
                                                onClick={handleConfirmRename} 
                                                className="p-1 text-green-400 hover:text-green-300 transition-colors"
                                                title="Confirm Rename"
                                            >
                                                <CheckIcon className="h-4 w-4" />
                                            </button>
                                            <button 
                                                onClick={handleCancelRename} 
                                                className="p-1 text-red-400 hover:text-red-300 transition-colors"
                                                title="Cancel Rename"
                                            >
                                                <XMarkIcon className="h-4 w-4" />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex-shrink-0 flex items-center space-x-2"> 
                                             <button 
                                                 onClick={() => handleStartRename(chat)}
                                                 className="p-1 text-gray-300 hover:text-accent hover:scale-110 transition-all duration-150 ease-in-out"
                                                 title="Rename Chat"
                                             >
                                                 <PencilIcon className="h-4 w-4" />
                                             </button>
                                             <button 
                                                 onClick={() => onDeleteChat(chat.id, chat.name)}
                                                 className="p-1 text-gray-300 hover:text-red-500 hover:scale-110 transition-all duration-150 ease-in-out"
                                                 title="Delete Chat"
                                             >
                                                 <TrashIcon className="h-4 w-4" />
                                             </button>
                                        </div>
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
} 