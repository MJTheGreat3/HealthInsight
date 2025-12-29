/**
 * WebSocket Service for real-time communication with the backend.
 * Handles chat functionality and real-time data synchronization.
 */

import { io, Socket } from "socket.io-client";
import { ChatMessage, WebSocketEvents } from "../types";

export class WebSocketService {
  private socket: Socket | null = null;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second

  constructor(private baseUrl: string = "http://localhost:8000") {}

  /**
   * Connect to WebSocket server with authentication token
   */
  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.baseUrl, {
          auth: { token },
          transports: ["websocket", "polling"],
          timeout: 10000,
        });

        this.socket.on("connect", () => {
          console.log("WebSocket connected");
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
        });

        this.socket.on("connected", (data: WebSocketEvents["connected"]) => {
          console.log("WebSocket authentication successful:", data);
          resolve();
        });

        this.socket.on("connect_error", (error) => {
          console.error("WebSocket connection error:", error);
          this.isConnected = false;
          reject(error);
        });

        this.socket.on("disconnect", (reason) => {
          console.log("WebSocket disconnected:", reason);
          this.isConnected = false;

          // Attempt to reconnect if not manually disconnected
          if (reason !== "io client disconnect") {
            this.attemptReconnect(token);
          }
        });

        this.socket.on("error", (error: WebSocketEvents["error"]) => {
          console.error("WebSocket error:", error);
        });
      } catch (error) {
        console.error("Failed to initialize WebSocket:", error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  getConnectionStatus(): boolean {
    return this.isConnected && this.socket?.connected === true;
  }

  /**
   * Start a chat session
   */
  startChat(): Promise<{ session_id: string; messages: ChatMessage[] }> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.isConnected) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      this.socket.emit("start_chat", {});

      const handleChatStarted = (data: WebSocketEvents["chat_started"]) => {
        this.socket?.off("chat_started", handleChatStarted);
        this.socket?.off("error", handleError);
        resolve(data);
      };

      const handleError = (error: WebSocketEvents["error"]) => {
        this.socket?.off("chat_started", handleChatStarted);
        this.socket?.off("error", handleError);
        reject(new Error(error.message));
      };

      this.socket.on("chat_started", handleChatStarted);
      this.socket.on("error", handleError);
    });
  }

  /**
   * Send a message in the chat
   */
  sendMessage(message: string): Promise<ChatMessage> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.isConnected) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      this.socket.emit("send_message", { message });

      const handleResponse = (data: WebSocketEvents["message_response"]) => {
        this.socket?.off("message_response", handleResponse);
        this.socket?.off("error", handleError);
        resolve(data);
      };

      const handleError = (error: WebSocketEvents["error"]) => {
        this.socket?.off("message_response", handleResponse);
        this.socket?.off("error", handleError);
        reject(new Error(error.message));
      };

      this.socket.on("message_response", handleResponse);
      this.socket.on("error", handleError);
    });
  }

  /**
   * End the current chat session
   */
  endChat(): void {
    if (this.socket && this.isConnected) {
      this.socket.emit("end_chat", {});
    }
  }

  /**
   * Subscribe to real-time data updates
   */
  subscribeToUpdates(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.isConnected) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      this.socket.emit("subscribe_updates", {});

      const handleSubscribed = () => {
        this.socket?.off("subscribed", handleSubscribed);
        this.socket?.off("error", handleError);
        resolve();
      };

      const handleError = (error: WebSocketEvents["error"]) => {
        this.socket?.off("subscribed", handleSubscribed);
        this.socket?.off("error", handleError);
        reject(new Error(error.message));
      };

      this.socket.on("subscribed", handleSubscribed);
      this.socket.on("error", handleError);
    });
  }

  /**
   * Listen for typing indicators
   */
  onTyping(callback: (isTyping: boolean) => void): void {
    if (this.socket) {
      this.socket.on("typing", (data: WebSocketEvents["typing"]) => {
        callback(data.typing);
      });
    }
  }

  /**
   * Listen for data updates
   */
  onDataUpdate(
    callback: (update: WebSocketEvents["data_update"]) => void
  ): void {
    if (this.socket) {
      this.socket.on("data_update", callback);
    }
  }

  /**
   * Listen for notifications
   */
  onNotification(
    callback: (notification: WebSocketEvents["notification"]) => void
  ): void {
    if (this.socket) {
      this.socket.on("notification", callback);
    }
  }

  /**
   * Listen for chat session end
   */
  onChatEnded(callback: (data: WebSocketEvents["chat_ended"]) => void): void {
    if (this.socket) {
      this.socket.on("chat_ended", callback);
    }
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(): void {
    if (this.socket) {
      this.socket.removeAllListeners();
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
    );

    setTimeout(() => {
      this.connect(token).catch((error) => {
        console.error("Reconnection failed:", error);
        // Double the delay for next attempt (exponential backoff)
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
      });
    }, this.reconnectDelay);
  }
}

// Create a singleton instance
export const websocketService = new WebSocketService();
