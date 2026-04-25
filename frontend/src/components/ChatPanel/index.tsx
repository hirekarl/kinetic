import React, { useState, useRef, useEffect } from 'react';

export interface Message {
  role: 'user' | 'system';
  content: string;
}

interface ChatPanelProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  messages: Message[];
}

const SUGGESTED_PROMPTS = [
  'Slept 5 hours, feeling stuck on laundry.',
  'I need help breaking down my triage list.',
  'Marcus vibe check: 4/10, saw him 11 days ago.',
];

export const ChatPanel: React.FC<ChatPanelProps> = ({ onSendMessage, isLoading, messages }) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-full flex-col border-r border-zinc-800 bg-zinc-950">
      {/* Dialogue Feed */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
        <header className="mb-8">
          <h1 className="mb-2 text-xl font-semibold text-zinc-100">Operational Liaison</h1>
          <p className="text-sm text-zinc-400 leading-relaxed">
            Executive Function Accessibility Mode Active. Brief Kinetic or request tactical
            micro-tasking.
          </p>
        </header>

        {messages.length === 0 && (
          <div className="space-y-4">
            <div className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Suggested Briefs
            </div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => {
                    setInput(prompt);
                  }}
                  className="text-left rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-zinc-800 text-zinc-100 rounded-tr-none'
                  : 'bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-tl-none font-mono'
              }`}
            >
              {msg.role === 'system' && (
                <span className="block text-[10px] font-bold text-emerald-500 mb-1 uppercase tracking-widest">
                  [SYSTEM READOUT]
                </span>
              )}
              {msg.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex gap-1">
                <div
                  className="h-1.5 w-1.5 rounded-full bg-zinc-700 animate-bounce"
                  style={{ animationDelay: '0ms' }}
                />
                <div
                  className="h-1.5 w-1.5 rounded-full bg-zinc-700 animate-bounce"
                  style={{ animationDelay: '150ms' }}
                />
                <div
                  className="h-1.5 w-1.5 rounded-full bg-zinc-700 animate-bounce"
                  style={{ animationDelay: '300ms' }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-zinc-800 bg-zinc-950">
        <form
          onSubmit={(e) => {
            handleSubmit(e);
          }}
          className="relative"
        >
          <textarea
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
            }}
            onKeyDown={handleKeyDown}
            placeholder="What's your status?"
            className="w-full min-h-[100px] max-h-[300px] resize-none rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 pb-12 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-700 focus:outline-none focus:ring-1 focus:ring-zinc-700"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute bottom-3 right-3 rounded-lg bg-zinc-100 px-4 py-1.5 text-xs font-semibold text-zinc-950 transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isLoading ? 'Analyzing...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
};
