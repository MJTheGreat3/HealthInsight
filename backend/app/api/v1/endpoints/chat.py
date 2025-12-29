"""
Chat endpoints for AI-powered health conversations.

This module provides REST API endpoints for managing chat sessions
and WebSocket integration for real-time communication.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.decorators import require_auth, require_patient
from app.services.chatbot import chatbot_service
from app.services.websocket import websocket_service
from app.models.chat import ChatMessage, ChatSession

router = APIRouter()


class ChatSessionResponse(BaseModel):
    """Response model for chat session data."""
    session_id: str
    patient_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class MessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str


class MessageResponse(BaseModel):
    """Response model for message data."""
    role: str
    content: str
    timestamp: str


@router.post("/sessions", response_model=ChatSessionResponse)
@require_auth
@require_patient
async def start_chat_session(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Start a new chat session or retrieve existing active session.
    
    Returns:
        ChatSessionResponse: Chat session data with message history
    """
    try:
        user_id = current_user["uid"]
        
        # Start or retrieve chat session
        chat_session = await chatbot_service.start_chat_session(user_id)
        
        # Convert messages to dict format
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in chat_session.messages
        ]
        
        return ChatSessionResponse(
            session_id=chat_session.id,
            patient_id=chat_session.patient_id,
            messages=messages,
            created_at=chat_session.created_at.isoformat(),
            updated_at=chat_session.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start chat session: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
@require_auth
@require_patient
async def send_message(
    session_id: str,
    message_request: MessageRequest,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Send a message to the chatbot and get AI response.
    
    Args:
        session_id: Chat session identifier
        message_request: Message content
        
    Returns:
        MessageResponse: AI assistant response
    """
    try:
        if not message_request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Process message through chatbot service
        ai_response = await chatbot_service.process_message(
            session_id,
            message_request.message
        )
        
        return MessageResponse(
            role=ai_response.role,
            content=ai_response.content,
            timestamp=ai_response.timestamp.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/sessions/{session_id}/history", response_model=List[MessageResponse])
@require_auth
@require_patient
async def get_chat_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get chat history for a session.
    
    Args:
        session_id: Chat session identifier
        
    Returns:
        List[MessageResponse]: List of chat messages
    """
    try:
        messages = await chatbot_service.get_chat_history(session_id)
        
        return [
            MessageResponse(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp.isoformat()
            )
            for msg in messages
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
@require_auth
@require_patient
async def end_chat_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    End a chat session.
    
    Args:
        session_id: Chat session identifier
        
    Returns:
        Dict: Success message
    """
    try:
        success = await chatbot_service.end_chat_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return {"message": "Chat session ended successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end chat session: {str(e)}"
        )


@router.get("/websocket/status")
@require_auth
async def get_websocket_status(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Get WebSocket service status and connection information.
    
    Returns:
        Dict: WebSocket service status
    """
    try:
        user_id = current_user["uid"]
        
        return {
            "service_status": "active",
            "total_connections": websocket_service.get_connection_count(),
            "user_online": websocket_service.is_user_online(user_id),
            "user_connections": websocket_service.get_user_connection_count(user_id),
            "active_users": len(websocket_service.get_active_users())
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket status: {str(e)}"
        )