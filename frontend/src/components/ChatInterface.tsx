/**
 * ChatInterface Component
 *
 * Provides a real-time chat interface for patients to interact with the AI chatbot.
 * Features include message display, typing indicators, and conversation history.
 */

import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "../types";
import { websocketService } from "../services/websocket";
import { useAuth } from "../hooks/useAuth";

interface ChatInterfaceProps {
  onClose?: () => void;
  className?: string;
}

export default function ChatInterface({
  onClose,
  className = "",
}: ChatInterfaceProps) {
  const { appUser, getIdToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize WebSocket connection and chat session
  useEffect(() => {
    const initializeChat = async () => {
      try {
        if (!appUser) return;

        // Get authentication token
        const token = await getIdToken();
        if (!token) {
          setError("Authentication failed");
          return;
        }

        // Connect to WebSocket
        await websocketService.connect(token);
        setIsConnected(true);

        // Set up event listeners
        websocketService.onTyping(setIsTyping);
        websocketService.onChatEnded(() => {
          setMessages([]);
        });

        // Start chat session
        const chatData = await websocketService.startChat();
        setMessages(chatData.messages);

        // Subscribe to real-time updates
        await websocketService.subscribeToUpdates();

        setError(null);
      } catch (err) {
        console.error("Failed to initialize chat:", err);
        setError(
          err instanceof Error ? err.message : "Failed to connect to chat"
        );
        setIsConnected(false);
      }
    };

    initializeChat();

    // Cleanup on unmount
    return () => {
      websocketService.removeAllListeners();
      websocketService.disconnect();
    };
  }, [appUser, getIdToken]);

  // Handle sending messages
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isSending || !isConnected) return;

    const messageContent = inputMessage.trim();
    setInputMessage("");
    setIsSending(true);

    // Add user message to display immediately
    const userMessage: ChatMessage = {
      role: "user",
      content: messageContent,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Send message through WebSocket
      const aiResponse = await websocketService.sendMessage(messageContent);
      setMessages((prev) => [...prev, aiResponse]);
      setError(null);
    } catch (err) {
      console.error("Failed to send message:", err);
      setError(err instanceof Error ? err.message : "Failed to send message");

      // Remove the user message if sending failed
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsSending(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle ending chat session
  const handleEndChat = () => {
    websocketService.endChat();
    if (onClose) {
      onClose();
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  if (!appUser || appUser.userType !== "patient") {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Chat Unavailable
          </h3>
          <p className="text-gray-600">
            Chat functionality is only available for patients.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Health Assistant
            </h3>
            <div className="flex items-center space-x-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-green-400" : "bg-red-400"
                }`}
              ></div>
              <span className="text-sm text-gray-500">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>
        </div>
        {onClose && (
          <button
            onClick={handleEndChat}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200">
          <div className="flex items-center space-x-2">
            <svg
              className="w-5 h-5 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-sm text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !error && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              Welcome to your Health Assistant
            </h4>
            <p className="text-gray-600 max-w-md mx-auto">
              I can help you understand your test results, provide lifestyle
              advice, and answer general health questions based on your medical
              history.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-900"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p
                className={`text-xs mt-1 ${
                  message.role === "user" ? "text-blue-100" : "text-gray-500"
                }`}
              >
                {formatTimestamp(message.timestamp)}
              </p>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                ></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isConnected ? "Ask me about your health..." : "Connecting..."
            }
            disabled={!isConnected || isSending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || !isConnected || isSending}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isSending ? (
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            ) : (
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
            <span>Send</span>
          </button>
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-gray-500 mt-2">
          This assistant provides general health information only. Always
          consult your healthcare provider for medical advice.
        </p>
      </div>
    </div>
  );
}
