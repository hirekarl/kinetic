import { useState, useEffect, useRef } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { streamCheckin, fetchHistory, completeTask } from '../api/client';
import type { AgentLogEntry, StreamDonePayload, SystemHealthPayload } from '../types';
import type { Message, RespondingAgent } from '../components/ChatPanel';
import { buildAgentLogEntry } from '../utils/agentLog';

/**
 * Return shape of the `useChat` hook, grouping all chat state and action callbacks
 * so `App` can spread them to child components without prop-drilling raw state setters.
 */
interface UseChatReturn {
  health: SystemHealthPayload | null;
  messages: Message[];
  agentLog: AgentLogEntry[];
  isLoading: boolean;
  error: string | null;
  lastMessage: string | null;
  streamingContent: string | null;
  handleSendMessage: (content: string) => void;
  handleRetry: () => void;
  handleCompleteTask: (taskName: string) => Promise<void>;
  handleReset: () => Promise<void>;
  setHealth: Dispatch<SetStateAction<SystemHealthPayload | null>>;
  setMessages: Dispatch<SetStateAction<Message[]>>;
  clearSession: () => void;
}

/**
 * Manages all chat interaction state for the Operational Liaison panel.
 *
 * On mount (or whenever `token` changes), hydrates the message list and the
 * latest `SystemHealthPayload` from the server's history endpoint so the
 * dashboard reflects the persisted state after a page refresh.
 *
 * Streaming check-ins are handled via `streamCheckin`: accumulated tokens drive
 * `streamingContent` for the in-progress bubble, and the final `done` event
 * commits the complete message to the `messages` list.
 *
 * @param token - JWT access token; when `null` the history fetch is skipped.
 * @returns `UseChatReturn` — state values and action handlers for the chat UI.
 */
export function useChat(token: string | null): UseChatReturn {
  const [health, setHealth] = useState<SystemHealthPayload | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [agentLog, setAgentLog] = useState<AgentLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const accumulatedRef = useRef('');

  useEffect(() => {
    if (!token) return;
    setIsLoading(true);
    void fetchHistory(token)
      .then((data) => {
        setHealth(data.health);
        setMessages(data.messages);
      })
      .catch((err: unknown) => {
        console.error('Failed to hydrate state', err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token]);

  const handleSendMessage = (content: string) => {
    setLastMessage(content);
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setIsLoading(true);
    setError(null);
    setStreamingContent('');
    accumulatedRef.current = '';

    const timestamp = new Date().toISOString();

    void streamCheckin(
      content,
      messages,
      token ?? undefined,
      (result) => {
        setHealth(result);
        setAgentLog((prev) => [buildAgentLogEntry(content, result, timestamp), ...prev]);
      },
      (text) => {
        accumulatedRef.current += text;
        setStreamingContent(accumulatedRef.current);
      },
      (done: StreamDonePayload) => {
        setIsLoading(false);
        setStreamingContent(null);
        setLastMessage(null);
        if (accumulatedRef.current) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'system',
              content: accumulatedRef.current,
              agent: (done.responding_agent as RespondingAgent | null) ?? 'liaison',
            },
          ]);
        }
      },
      (detail: string) => {
        setIsLoading(false);
        setStreamingContent(null);
        setError(detail);
        setMessages((prev) => [
          ...prev,
          { role: 'system', content: `Check-in could not be processed. ${detail}` },
        ]);
      }
    );
  };

  const handleRetry = () => {
    if (lastMessage) {
      setError(null);
      handleSendMessage(lastMessage);
    }
  };

  const handleCompleteTask = async (taskName: string): Promise<void> => {
    try {
      await completeTask(taskName, token ?? undefined);
      if (token) {
        const data = await fetchHistory(token);
        setHealth(data.health);
      }
    } catch (err) {
      console.error('Failed to complete task', err);
    }
  };

  const handleReset = async (): Promise<void> => {
    if (!confirm('Are you sure you want to wipe all system data? This cannot be undone.')) return;
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/debug/reset`,
        {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      if (response.ok) {
        setHealth(null);
        setMessages([]);
        setError(null);
        setLastMessage(null);
      }
    } catch (err) {
      console.error('Reset failed', err);
    }
  };

  const clearSession = () => {
    setHealth(null);
    setMessages([]);
    setAgentLog([]);
    setError(null);
    setLastMessage(null);
  };

  return {
    health,
    messages,
    agentLog,
    isLoading,
    error,
    lastMessage,
    streamingContent,
    handleSendMessage,
    handleRetry,
    handleCompleteTask,
    handleReset,
    setHealth,
    setMessages,
    clearSession,
  };
}
