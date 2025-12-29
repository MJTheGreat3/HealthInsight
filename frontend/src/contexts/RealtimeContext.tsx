/**
 * RealtimeContext
 *
 * Provides real-time data synchronization across the application using WebSocket connections.
 * Handles data updates, notifications, and connection management.
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { websocketService } from "../services/websocket";
import { useAuth } from "../hooks/useAuth";

interface DataUpdate {
  type: string;
  data: any;
  timestamp: string;
}

interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface RealtimeContextType {
  isConnected: boolean;
  notifications: Notification[];
  connectionError: string | null;
  addNotification: (
    notification: Omit<Notification, "id" | "timestamp" | "read">
  ) => void;
  markNotificationAsRead: (id: string) => void;
  clearNotifications: () => void;
  subscribeToDataUpdates: (
    callback: (update: DataUpdate) => void
  ) => () => void;
  reconnect: () => Promise<void>;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(
  undefined
);

interface RealtimeProviderProps {
  children: React.ReactNode;
}

export function RealtimeProvider({ children }: RealtimeProviderProps) {
  const { appUser, getIdToken } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [dataUpdateCallbacks, setDataUpdateCallbacks] = useState<
    Set<(update: DataUpdate) => void>
  >(new Set());

  // Generate unique notification ID
  const generateNotificationId = () => {
    return `notification_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;
  };

  // Add notification
  const addNotification = useCallback(
    (notification: Omit<Notification, "id" | "timestamp" | "read">) => {
      const newNotification: Notification = {
        ...notification,
        id: generateNotificationId(),
        timestamp: new Date().toISOString(),
        read: false,
      };

      setNotifications((prev) => [newNotification, ...prev]);

      // Auto-remove info notifications after 5 seconds
      if (notification.type === "info") {
        setTimeout(() => {
          setNotifications((prev) =>
            prev.filter((n) => n.id !== newNotification.id)
          );
        }, 5000);
      }
    },
    []
  );

  // Mark notification as read
  const markNotificationAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  }, []);

  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Subscribe to data updates
  const subscribeToDataUpdates = useCallback(
    (callback: (update: DataUpdate) => void) => {
      setDataUpdateCallbacks((prev) => new Set([...prev, callback]));

      // Return unsubscribe function
      return () => {
        setDataUpdateCallbacks((prev) => {
          const newSet = new Set(prev);
          newSet.delete(callback);
          return newSet;
        });
      };
    },
    []
  );

  // Initialize WebSocket connection
  const initializeConnection = useCallback(async () => {
    if (!appUser) return;

    try {
      const token = await getIdToken();
      if (!token) {
        setConnectionError("Authentication failed");
        return;
      }

      // Connect to WebSocket
      await websocketService.connect(token);
      setIsConnected(true);
      setConnectionError(null);

      // Subscribe to real-time updates
      await websocketService.subscribeToUpdates();

      // Set up data update listener
      websocketService.onDataUpdate((update) => {
        console.log("Received data update:", update);

        // Notify all subscribers
        dataUpdateCallbacks.forEach((callback) => {
          try {
            callback(update);
          } catch (error) {
            console.error("Error in data update callback:", error);
          }
        });

        // Add notification for certain update types
        if (update.type === "report_uploaded") {
          addNotification({
            type: "success",
            title: "New Report Processed",
            message: "Your medical report has been successfully analyzed.",
          });
        } else if (update.type === "metrics_updated") {
          addNotification({
            type: "info",
            title: "Metrics Updated",
            message: "Your tracked metrics have been updated with new data.",
          });
        }
      });

      // Set up notification listener
      websocketService.onNotification((notification) => {
        console.log("Received notification:", notification);

        addNotification({
          type: "info",
          title: notification.notification.title || "System Notification",
          message:
            notification.notification.message || "You have a new notification.",
        });
      });

      console.log("Real-time connection initialized successfully");
    } catch (error) {
      console.error("Failed to initialize real-time connection:", error);
      setConnectionError(
        error instanceof Error ? error.message : "Connection failed"
      );
      setIsConnected(false);
    }
  }, [appUser, getIdToken, dataUpdateCallbacks, addNotification]);

  // Reconnect function
  const reconnect = useCallback(async () => {
    setConnectionError(null);
    await initializeConnection();
  }, [initializeConnection]);

  // Initialize connection when user changes
  useEffect(() => {
    if (appUser) {
      initializeConnection();
    } else {
      // Clean up when appUser logs out
      websocketService.disconnect();
      setIsConnected(false);
      setNotifications([]);
      setConnectionError(null);
    }

    // Cleanup on unmount
    return () => {
      websocketService.removeAllListeners();
      websocketService.disconnect();
    };
  }, [appUser, initializeConnection]);

  // Monitor connection status
  useEffect(() => {
    const checkConnection = () => {
      const connected = websocketService.getConnectionStatus();
      if (connected !== isConnected) {
        setIsConnected(connected);

        if (!connected && appUser) {
          setConnectionError("Connection lost. Attempting to reconnect...");
          // Attempt to reconnect after a short delay
          setTimeout(reconnect, 2000);
        }
      }
    };

    const interval = setInterval(checkConnection, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, [isConnected, appUser, reconnect]);

  const value: RealtimeContextType = {
    isConnected,
    notifications,
    connectionError,
    addNotification,
    markNotificationAsRead,
    clearNotifications,
    subscribeToDataUpdates,
    reconnect,
  };

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (context === undefined) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}
