/**
 * ChatPage Component
 *
 * A full-page chat interface for patients who prefer a dedicated chat experience.
 * Includes navigation back to the dashboard.
 */

import { useNavigate } from "react-router-dom";
import ChatInterface from "./ChatInterface";
import { useAuth } from "../hooks/useAuth";

export default function ChatPage() {
  const navigate = useNavigate();
  const { appUser } = useAuth();

  const handleClose = () => {
    navigate("/patient/dashboard");
  };

  if (!appUser || appUser.userType !== "patient") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Access Denied
          </h2>
          <p className="text-gray-600 mb-4">
            Chat functionality is only available for patients.
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleClose}
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
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <h1 className="text-xl font-semibold text-gray-900">
                Health Assistant Chat
              </h1>
            </div>

            <nav className="flex space-x-4">
              <button
                onClick={() => navigate("/patient/dashboard")}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Dashboard
              </button>
              <button
                onClick={() => navigate("/patient/history")}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Reports
              </button>
              <button
                onClick={() => navigate("/patient/profile")}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Profile
              </button>
            </nav>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto p-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-[calc(100vh-8rem)]">
          <ChatInterface onClose={handleClose} className="h-full" />
        </div>
      </div>
    </div>
  );
}
