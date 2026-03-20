"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import Button from "./ui/Button";
import Spinner from "./ui/Spinner";
import { sendChatMessage, clearChat, type ChatMessage } from "@/lib/api";

interface ChatPanelProps {
  username: string;
  initialMessage?: string;
}

const SUGGESTED_PROMPTS = [
  "What is my biggest weakness?",
  "Why do I lose more with Black?",
  "What should I study next?",
  "How can I improve my openings?",
  "Show me my worst mistakes",
];

export default function ChatPanel({ username, initialMessage }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const processedInitialRef = useRef<string | undefined>(undefined);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;

      const userMsg: ChatMessage = { role: "user", content: text.trim() };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      try {
        const response = await sendChatMessage(username, text.trim());
        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: response,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errorMsg: ChatMessage = {
          role: "assistant",
          content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : "Unknown error"}. Please try again.`,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [loading, username]
  );

  // Handle initial message from "Explain this mistake"
  useEffect(() => {
    if (initialMessage && initialMessage !== processedInitialRef.current) {
      processedInitialRef.current = initialMessage;
      sendMessage(initialMessage);
    }
  }, [initialMessage, sendMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleClear = async () => {
    setClearing(true);
    try {
      await clearChat(username);
      setMessages([]);
    } catch {
      // Ignore clear errors
    } finally {
      setClearing(false);
    }
  };

  const handleSuggestion = (prompt: string) => {
    sendMessage(prompt);
  };

  return (
    <div className="flex h-full flex-col rounded-xl border border-chess-surface-light bg-chess-surface/80 shadow-lg backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-chess-surface-light px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">♟</span>
          <h3 className="font-semibold text-white">AI Chess Coach</h3>
        </div>
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            loading={clearing}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center gap-4 py-8">
            <div className="text-4xl">🎓</div>
            <p className="text-center text-sm text-gray-400">
              Ask your AI coach anything about your chess games
            </p>
            <div className="flex flex-col gap-2 w-full">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSuggestion(prompt)}
                  className="rounded-lg border border-chess-surface-light bg-chess-dark/50 px-3 py-2 text-left text-sm text-gray-300 transition-colors hover:border-chess-accent/50 hover:text-white"
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
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-chess-accent text-white"
                  : "bg-chess-surface-light text-gray-200"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-strong:text-white prose-code:text-chess-gold prose-code:bg-chess-dark prose-code:px-1 prose-code:rounded">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-xl bg-chess-surface-light px-4 py-3">
              <Spinner size="sm" />
              <span className="text-sm text-gray-400">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-chess-surface-light p-3"
      >
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your chess coach..."
            disabled={loading}
            className="flex-1 rounded-lg border border-chess-surface-light bg-chess-dark px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-chess-accent focus:outline-none focus:ring-1 focus:ring-chess-accent disabled:opacity-50"
          />
          <Button type="submit" size="sm" disabled={!input.trim() || loading}>
            Send
          </Button>
        </div>
      </form>
    </div>
  );
}
