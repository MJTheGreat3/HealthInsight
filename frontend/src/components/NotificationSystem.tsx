/**
 * NotificationSystem Component
 *
 * Displays real-time notifications as toast messages.
 * Handles different notification types with appropriate styling and auto-dismiss.
 */

import { useEffect, useState } from "react";
import { useRealtime } from "../contexts/RealtimeContext";

interface NotificationToastProps {
  notification: {
    id: string;
    type: "info" | "success" | "warning" | "error";
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
  };
  onClose: (id: string) => void;
  onMarkAsRead: (id: string) => void;
}

function NotificationToast({
  notification,
  onClose,
  onMarkAsRead,
}: NotificationToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  // Animate in
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Auto-dismiss for info notifications
  useEffect(() => {
    if (notification.type === "info") {
      const timer = setTimeout(() => {
        handleClose();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification.type]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(notification.id);
    }, 300);
  };

  const handleClick = () => {
    if (!notification.read) {
      onMarkAsRead(notification.id);
    }
  };

  const getNotificationStyles = () => {
    const baseStyles = "border-l-4 shadow-lg";

    switch (notification.type) {
      case "success":
        return `${baseStyles} bg-green-50 border-green-400`;
      case "warning":
        return `${baseStyles} bg-yellow-50 border-yellow-400`;
      case "error":
        return `${baseStyles} bg-red-50 border-red-400`;
      default:
        return `${baseStyles} bg-blue-50 border-blue-400`;
    }
  };

  const getIconStyles = () => {
    switch (notification.type) {
      case "success":
        return "text-green-400";
      case "warning":
        return "text-yellow-400";
      case "error":
        return "text-red-400";
      default:
        return "text-blue-400";
    }
  };

  const getIcon = () => {
    switch (notification.type) {
      case "success":
        return (
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
              d="M5 13l4 4L19 7"
            />
          </svg>
        );
      case "warning":
        return (
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
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        );
      case "error":
        return (
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
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      default:
        return (
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
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
    }
  };

  return (
    <div
      className={`
        max-w-sm w-full bg-white rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden
        transform transition-all duration-300 ease-in-out
        ${
          isVisible && !isExiting
            ? "translate-x-0 opacity-100"
            : "translate-x-full opacity-0"
        }
        ${getNotificationStyles()}
      `}
      onClick={handleClick}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className={`flex-shrink-0 ${getIconStyles()}`}>{getIcon()}</div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            <p className="text-sm font-medium text-gray-900">
              {notification.title}
            </p>
            <p className="mt-1 text-sm text-gray-500">{notification.message}</p>
            <p className="mt-1 text-xs text-gray-400">
              {new Date(notification.timestamp).toLocaleTimeString()}
            </p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              onClick={(e) => {
                e.stopPropagation();
                handleClose();
              }}
            >
              <span className="sr-only">Close</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NotificationSystem() {
  const { notifications, markNotificationAsRead } = useRealtime();
  const [visibleNotifications, setVisibleNotifications] = useState<
    typeof notifications
  >([]);

  // Update visible notifications when notifications change
  useEffect(() => {
    setVisibleNotifications(notifications.slice(0, 5)); // Show max 5 notifications
  }, [notifications]);

  const handleCloseNotification = (id: string) => {
    setVisibleNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      {visibleNotifications.map((notification) => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onClose={handleCloseNotification}
          onMarkAsRead={markNotificationAsRead}
        />
      ))}
    </div>
  );
}
