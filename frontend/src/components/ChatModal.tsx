/**
 * ChatModal Component
 *
 * A modal wrapper for the ChatInterface that can be opened from anywhere in the app.
 * Provides a floating chat experience for patients.
 */

import ChatInterface from "./ChatInterface";

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatModal({ isOpen, onClose }: ChatModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="absolute bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden">
        <ChatInterface onClose={onClose} className="h-full" />
      </div>
    </div>
  );
}
