'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // Ensure consistent markdown flavor

interface PrdViewProps {
    markdown: string;
    isLoading: boolean;
}

export default function PrdView({ markdown, isLoading }: PrdViewProps) {
    return (
        <div className="prose prose-lg prose-invert max-w-none h-full text-gray-200">
            <h3 className="text-xl font-semibold mb-4 border-b pb-2 border-dark-700 text-gray-100">Generated PRD Preview</h3>
            {isLoading ? (
                <p className="text-gray-400 italic">Loading PRD content...</p>
            ) : !markdown ? (
                <p className="text-gray-400 italic">PRD content will appear here as the chat progresses.</p>
            ) : (
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  // Apply styling via prose-invert, customize links etc.
                  components={{
                        // Customize heading styles further if prose-lg isn't enough
                        h1: ({ ...props}) => <h1 {...props} className="text-2xl font-bold mb-6 text-accent"/>,
                        h2: ({ ...props}) => <h2 {...props} className="text-xl font-semibold mt-8 mb-4 pb-1 border-b border-dark-700"/>,
                        h3: ({ ...props}) => <h3 {...props} className="text-lg font-semibold mt-6 mb-3"/>,
                        // Customize list spacing
                        ul: ({ ...props}) => <ul {...props} className="space-y-2"/>,
                        ol: ({ ...props}) => <ol {...props} className="space-y-2"/>,
                        // Link styling
                        a: ({ ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline"/>,
                        // Code block styling
                        pre: ({ ...props}) => <pre {...props} className="bg-dark-900 p-3 rounded text-sm" />,
                        code: (props: { inline?: boolean; className?: string; children?: React.ReactNode }) => {
                            const { inline, className, children } = props;
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              // Block code
                              <code className={className} {...props}>{children}</code>
                            ) : (
                              // Inline code
                              <code className="bg-dark-700 text-accent px-1.5 py-0.5 rounded text-sm" {...props}>{children}</code>
                            );
                        },
                         // Improve paragraph spacing
                         p: ({ ...props}) => <p {...props} className="my-3 leading-relaxed"/>
                  }}
                >
                    {markdown}
                </ReactMarkdown>
            )}
        </div>
    );
} 