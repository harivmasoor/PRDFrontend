'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/types/chat';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatViewProps {
    messages: ChatMessage[];
    onSendMessage: (content: string) => Promise<void>;
    isLoading: boolean;
    isSending: boolean;
}

export default function ChatView({ 
    messages, 
    onSendMessage, 
    isLoading,
    isSending
}: ChatViewProps) {
    const [inputMessage, setInputMessage] = useState<string>('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom when messages change or initially load
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async () => {
        const trimmedMessage = inputMessage.trim();
        if (!trimmedMessage || isSending) return;
        setInputMessage(''); // Clear input immediately
        await onSendMessage(trimmedMessage);
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Submit on Enter, allow Shift+Enter for newline
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent default newline insertion
            handleSendMessage();
        }
    };

    const formatMessageContent = (role: string, content: string) => {
        // Basic formatting - render markdown for assistant messages
        // Add more sophisticated styling or rendering logic here
        return (
           <ReactMarkdown 
             remarkPlugins={[remarkGfm]}
             components={{
                // Customize rendering of elements if needed, e.g., links, code blocks
                // Example: Style code blocks
                code(props: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                  const { inline, className, children } = props;
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <pre className="bg-gray-100 dark:bg-gray-700 p-2 rounded my-2 overflow-x-auto"><code className={className} {...props}>{children}</code></pre>
                  ) : (
                    <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-sm" {...props}>{children}</code>
                  );
                },
                // Example: Style paragraphs
                p({ node, children }) {
                    // Avoid extra margins for paragraphs within list items, etc.
                    if (node?.position?.start.line !== node?.position?.end.line) {
                       return <p className="mb-2 last:mb-0">{children}</p>;
                    }
                    return <>{children}</>;
                }
              }}
           >
                {content}
           </ReactMarkdown>
        )
    };

    return (
        <div className="flex flex-col h-full bg-dark-900">
            {/* Message Display Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {isLoading ? (
                    <div className="text-center text-gray-400">Loading messages...</div>
                ) : messages.length === 0 ? (
                     <div className="text-center text-gray-400">No messages yet. Send one below!</div>
                 ) : (
                    messages.map((msg, index) => (
                        <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div 
                                className={`rounded-lg px-4 py-2 max-w-xl break-words text-sm lg:text-base ${ 
                                    msg.role === 'user' 
                                        ? 'bg-accent text-white font-semibold' /* User: Cyan bg, WHITE BOLD text */
                                        : msg.role === 'assistant'
                                        ? 'bg-dark-700 text-gray-100' /* Assistant: Darker gray */
                                        : 'bg-yellow-900/50 text-yellow-300 text-xs italic' /* System: Muted yellow */
                                }`}
                            >
                               {/* Render simple text for user/system, markdown for assistant */} 
                                {msg.role === 'assistant' 
                                   ? formatMessageContent(msg.role, msg.content) 
                                   : <p>{msg.content}</p> // Keep user/system as plain text paragraphs
                                } 
                            </div>
                        </div>
                    ))
                 )
                }
                {/* Invisible element to scroll to */} 
                <div ref={messagesEndRef} /> 
            </div>

            {/* Message Input Area */}
            <div className="p-4 border-t border-dark-700 bg-dark-900">
                <div className="flex items-center bg-dark-700 rounded-lg px-2 py-1">
                    <textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Send a message to build your PRD..."
                        className="flex-grow bg-transparent border-none focus:ring-0 resize-none outline-none p-2 text-sm text-gray-100 placeholder-gray-400"
                        rows={1} // Start with 1 row, grows automatically?
                        disabled={isSending || isLoading}
                        // Consider adding auto-grow behavior with JS if needed
                    />
                    <button 
                        onClick={handleSendMessage}
                        disabled={isSending || !inputMessage.trim()}
                        className={`ml-2 p-2 rounded-full transition-colors ${isSending || !inputMessage.trim() ? 'text-gray-500 cursor-not-allowed' : 'text-accent hover:bg-dark-700'}`}
                        title="Send Message"
                    >
                        <PaperAirplaneIcon className="h-5 w-5" />
                    </button>
                </div>
            </div>
        </div>
    );
} 