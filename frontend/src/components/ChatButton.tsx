/**
 * ChatButton Component
 *
 * A floating action button that opens the chat interface.
 * Only visible for authenticated patients.
 */

import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import ChatModal from "./ChatModal";

interface ChatButtonProps {
  className?: string;
}

export default function ChatButton({ className = "" }: ChatButtonProps) {
  const { appUser } = useAuth();
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Only show for patients
  if (!appUser || appUser.userType !== "patient") {
    return null;
  }

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsChatOpen(true)}
        className={`fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center z-40 ${className}`}
        title="Open Health Assistant Chat"
      >
        <svg
          className="w-6 h-6"
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

        {/* Notification dot (could be used for unread messages) */}
        {/* <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div> */}
      </button>

      {/* Chat Modal */}
      <ChatModal isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </>
  );
}
