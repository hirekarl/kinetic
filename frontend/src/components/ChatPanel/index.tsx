import React, { useState } from 'react';

interface ChatPanelProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const SUGGESTED_PROMPTS = [
  'Slept 5 hours, ate okay, feeling energized.',
  'Laundry is 2 days overdue, high priority.',
  'Marcus vibe check: 8/10, saw him yesterday.',
];

export const ChatPanel: React.FC<ChatPanelProps> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-full flex-col border-r border-zinc-800 bg-zinc-950 p-6">
      <div className="flex-1 overflow-y-auto pb-4">
        <h1 className="mb-2 text-xl font-semibold text-zinc-100">Brief Kinetic</h1>
        <p className="mb-8 text-sm text-zinc-400">Update your system status in natural language.</p>

        <div className="space-y-4">
          <div className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Suggested Prompts
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => {
                  setMessage(prompt);
                }}
                className="rounded-full border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <form
        onSubmit={(e) => {
          handleSubmit(e);
        }}
        className="mt-auto"
      >
        <div className="relative">
          <textarea
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
            }}
            onKeyDown={handleKeyDown}
            placeholder="What's your status?"
            className="w-full min-h-[120px] resize-none rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-700 focus:outline-none focus:ring-1 focus:ring-zinc-700"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !message.trim()}
            className="absolute bottom-3 right-3 rounded-lg bg-zinc-100 px-4 py-1.5 text-xs font-semibold text-zinc-950 transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isLoading ? 'Analyzing...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
};
