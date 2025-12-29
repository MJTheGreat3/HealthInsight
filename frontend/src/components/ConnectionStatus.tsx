/**
 * ConnectionStatus Component
 *
 * Displays the real-time connection status and provides reconnection functionality.
 * Shows as a small indicator that can be expanded for more details.
 */

import { useState } from "react";
import { useRealtime } from "../contexts/RealtimeContext";

interface ConnectionStatusProps {
  className?: string;
}

export default function ConnectionStatus({
  className = "",
}: ConnectionStatusProps) {
  const { isConnected, connectionError, reconnect } = useRealtime();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await reconnect();
    } catch (error) {
      console.error("Reconnection failed:", error);
    } finally {
      setIsReconnecting(false);
    }
  };

  const getStatusColor = () => {
    if (isConnected) return "bg-green-400";
    if (connectionError) return "bg-red-400";
    return "bg-yellow-400";
  };

  const getStatusText = () => {
    if (isConnected) return "Connected";
    if (connectionError) return "Disconnected";
    return "Connecting...";
  };

  return (
    <div className={`relative ${className}`}>
      {/* Status Indicator */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center space-x-2 px-3 py-1 bg-white rounded-full shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
        title={`Real-time status: ${getStatusText()}`}
      >
        <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
        <span className="text-xs text-gray-600 hidden sm:inline">
          {getStatusText()}
        </span>
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Expanded Status Panel */}
      {isExpanded && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">
                Real-time Connection
              </h4>
              <button
                onClick={() => setIsExpanded(false)}
                className="text-gray-400 hover:text-gray-600"
              >
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
              <span className="text-sm text-gray-700">{getStatusText()}</span>
            </div>

            {connectionError && (
              <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                {connectionError}
              </div>
            )}

            <div className="text-xs text-gray-500">
              {isConnected ? (
                <div className="space-y-1">
                  <p>✓ Real-time updates enabled</p>
                  <p>✓ Chat functionality available</p>
                  <p>✓ Instant notifications</p>
                </div>
              ) : (
                <div className="space-y-1">
                  <p>✗ Real-time updates disabled</p>
                  <p>✗ Chat functionality limited</p>
                  <p>✗ Manual refresh required</p>
                </div>
              )}
            </div>

            {!isConnected && (
              <button
                onClick={handleReconnect}
                disabled={isReconnecting}
                className="w-full px-3 py-2 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-1"
              >
                {isReconnecting ? (
                  <>
                    <svg
                      className="w-3 h-3 animate-spin"
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
                    <span>Reconnecting...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-3 h-3"
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
                    <span>Reconnect</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
