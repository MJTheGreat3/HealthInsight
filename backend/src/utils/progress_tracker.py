"""
Progress tracking utility for real-time upload processing updates
"""
import time
import threading
from typing import Dict, Any, Optional
from enum import Enum


class ProcessingStage(Enum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    OCR_PROCESSING = "ocr_processing"
    LLM_PARSING = "llm_parsing"
    LLM_ANALYZING = "llm_analyzing"
    SAVING = "saving"
    COMPLETE = "complete"
    FAILED = "failed"


class ProgressTracker:
    """Thread-safe progress tracker for upload processing"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_session(self, session_id: str, file_name: str) -> None:
        """Create a new tracking session"""
        with self._lock:
            self._sessions[session_id] = {
                "session_id": session_id,
                "file_name": file_name,
                "stage": ProcessingStage.UPLOADING,
                "progress": 0,
                "message": "Starting upload...",
                "start_time": time.time(),
                "estimated_total": 120,  # Default 2 minutes
                "method": "fast_extraction",  # Default assumption
                "error": None,
                "updated_at": time.time()
            }
    
    def update_progress(self, session_id: str, stage: ProcessingStage, 
                     progress: int, message: str, method: str = None, error: str = None) -> None:
        """Update progress for a session"""
        with self._lock:
            if session_id not in self._sessions:
                return
            
            session = self._sessions[session_id]
            session["stage"] = stage
            session["progress"] = min(100, max(0, progress))
            session["message"] = message
            session["updated_at"] = time.time()
            
            if method:
                session["method"] = method
            
            if error:
                session["error"] = error
                session["stage"] = ProcessingStage.FAILED
            
            # Update estimated time based on stage and progress rate
            elapsed = session["updated_at"] - session["start_time"]
            if progress > 0:
                session["estimated_total"] = (elapsed / progress) * 100
    
    def complete_session(self, session_id: str, final_data: Dict[str, Any] = None) -> None:
        """Mark session as complete"""
        self.update_progress(session_id, ProcessingStage.COMPLETE, 100, "Processing complete")
        
        if final_data:
            with self._lock:
                if session_id in self._sessions:
                    self._sessions[session_id].update(final_data)
    
    def fail_session(self, session_id: str, error: str) -> None:
        """Mark session as failed"""
        self.update_progress(session_id, ProcessingStage.FAILED, 0, "Processing failed", error=error)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            return self._sessions.get(session_id)
    
    def cleanup_session(self, session_id: str) -> None:
        """Remove session after completion"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions"""
        with self._lock:
            return self._sessions.copy()


# Global progress tracker instance
progress_tracker = ProgressTracker()