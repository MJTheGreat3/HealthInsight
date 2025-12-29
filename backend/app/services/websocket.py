"""
WebSocket Service for real-time communication and data synchronization.

This service handles WebSocket connections for chat functionality and real-time
data updates across the application.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import json

import socketio
from fastapi import HTTPException

from app.services.chatbot import ChatbotService
from app.services.auth import AuthService
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for managing WebSocket connections and real-time communication."""
    
    def __init__(self, chatbot_service: ChatbotService, auth_service: AuthService):
        """Initialize WebSocket service with Socket.IO server."""
        self.chatbot_service = chatbot_service
        self.auth_service = auth_service
        
        # Create Socket.IO server with CORS settings
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",  # Configure appropriately for production
            logger=True,
            engineio_logger=True
        )
        
        # Track active connections
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> connection_info
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        
        # Register event handlers
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register Socket.IO event handlers."""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection."""
            try:
                logger.info(f"Client {sid} attempting to connect")
                
                # Authenticate user
                if not auth or 'token' not in auth:
                    logger.warning(f"Client {sid} connection rejected: No auth token")
                    await self.sio.disconnect(sid)
                    return False
                
                # Verify Firebase token
                user_data = await self.auth_service.verify_token(auth['token'])
                if not user_data:
                    logger.warning(f"Client {sid} connection rejected: Invalid token")
                    await self.sio.disconnect(sid)
                    return False
                
                user_id = user_data.get('uid')
                user_type = user_data.get('user_type', 'patient')
                
                # Store connection info
                self.active_sessions[sid] = {
                    'user_id': user_id,
                    'user_type': user_type,
                    'connected_at': datetime.utcnow(),
                    'chat_session_id': None
                }
                
                # Track user sessions
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(sid)
                
                logger.info(f"Client {sid} connected as user {user_id} ({user_type})")
                
                # Send connection confirmation
                await self.sio.emit('connected', {
                    'status': 'connected',
                    'user_id': user_id,
                    'user_type': user_type,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                return True
                
            except Exception as e:
                logger.error(f"Error during client {sid} connection: {str(e)}")
                await self.sio.disconnect(sid)
                return False
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            try:
                if sid in self.active_sessions:
                    session_info = self.active_sessions[sid]
                    user_id = session_info.get('user_id')
                    
                    # Remove from user sessions
                    if user_id and user_id in self.user_sessions:
                        self.user_sessions[user_id].discard(sid)
                        if not self.user_sessions[user_id]:
                            del self.user_sessions[user_id]
                    
                    # Clean up session
                    del self.active_sessions[sid]
                    
                    logger.info(f"Client {sid} (user {user_id}) disconnected")
                
            except Exception as e:
                logger.error(f"Error during client {sid} disconnection: {str(e)}")
        
        @self.sio.event
        async def start_chat(sid, data):
            """Handle chat session start request."""
            try:
                if sid not in self.active_sessions:
                    await self.sio.emit('error', {
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                session_info = self.active_sessions[sid]
                user_id = session_info['user_id']
                user_type = session_info['user_type']
                
                # Only patients can start chat sessions
                if user_type != 'patient':
                    await self.sio.emit('error', {
                        'message': 'Chat is only available for patients'
                    }, room=sid)
                    return
                
                # Start or retrieve chat session
                chat_session = await self.chatbot_service.start_chat_session(user_id)
                
                # Update connection info
                self.active_sessions[sid]['chat_session_id'] = chat_session.id
                
                # Send chat session info
                await self.sio.emit('chat_started', {
                    'session_id': chat_session.id,
                    'messages': [
                        {
                            'role': msg.role,
                            'content': msg.content,
                            'timestamp': msg.timestamp.isoformat()
                        }
                        for msg in chat_session.messages
                    ]
                }, room=sid)
                
                logger.info(f"Started chat session {chat_session.id} for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error starting chat for client {sid}: {str(e)}")
                await self.sio.emit('error', {
                    'message': 'Failed to start chat session'
                }, room=sid)
        
        @self.sio.event
        async def send_message(sid, data):
            """Handle chat message from client."""
            try:
                if sid not in self.active_sessions:
                    await self.sio.emit('error', {
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                session_info = self.active_sessions[sid]
                chat_session_id = session_info.get('chat_session_id')
                
                if not chat_session_id:
                    await self.sio.emit('error', {
                        'message': 'No active chat session'
                    }, room=sid)
                    return
                
                message_content = data.get('message', '').strip()
                if not message_content:
                    await self.sio.emit('error', {
                        'message': 'Message cannot be empty'
                    }, room=sid)
                    return
                
                # Send typing indicator
                await self.sio.emit('typing', {'typing': True}, room=sid)
                
                # Process message through chatbot service
                ai_response = await self.chatbot_service.process_message(
                    chat_session_id,
                    message_content
                )
                
                # Stop typing indicator
                await self.sio.emit('typing', {'typing': False}, room=sid)
                
                # Send AI response
                await self.sio.emit('message_response', {
                    'role': ai_response.role,
                    'content': ai_response.content,
                    'timestamp': ai_response.timestamp.isoformat()
                }, room=sid)
                
                logger.info(f"Processed message in chat session {chat_session_id}")
                
            except Exception as e:
                logger.error(f"Error processing message for client {sid}: {str(e)}")
                await self.sio.emit('typing', {'typing': False}, room=sid)
                await self.sio.emit('error', {
                    'message': 'Failed to process message'
                }, room=sid)
        
        @self.sio.event
        async def end_chat(sid, data):
            """Handle chat session end request."""
            try:
                if sid not in self.active_sessions:
                    return
                
                session_info = self.active_sessions[sid]
                chat_session_id = session_info.get('chat_session_id')
                
                if chat_session_id:
                    await self.chatbot_service.end_chat_session(chat_session_id)
                    self.active_sessions[sid]['chat_session_id'] = None
                    
                    await self.sio.emit('chat_ended', {
                        'session_id': chat_session_id
                    }, room=sid)
                    
                    logger.info(f"Ended chat session {chat_session_id}")
                
            except Exception as e:
                logger.error(f"Error ending chat for client {sid}: {str(e)}")
        
        @self.sio.event
        async def subscribe_updates(sid, data):
            """Handle subscription to real-time data updates."""
            try:
                if sid not in self.active_sessions:
                    await self.sio.emit('error', {
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                session_info = self.active_sessions[sid]
                user_id = session_info['user_id']
                
                # Join user-specific room for updates
                await self.sio.enter_room(sid, f"user_{user_id}")
                
                await self.sio.emit('subscribed', {
                    'message': 'Subscribed to real-time updates'
                }, room=sid)
                
                logger.info(f"User {user_id} subscribed to real-time updates")
                
            except Exception as e:
                logger.error(f"Error subscribing to updates for client {sid}: {str(e)}")
    
    async def broadcast_data_update(
        self,
        user_id: str,
        update_type: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast data update to all user sessions.
        
        Args:
            user_id: User to send update to
            update_type: Type of update (report_uploaded, metrics_updated, etc.)
            data: Update data
        """
        try:
            update_message = {
                'type': update_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send to user-specific room
            await self.sio.emit(
                'data_update',
                update_message,
                room=f"user_{user_id}"
            )
            
            logger.info(f"Broadcasted {update_type} update to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting update to user {user_id}: {str(e)}")
    
    async def broadcast_system_notification(
        self,
        user_id: str,
        notification: Dict[str, Any]
    ):
        """
        Send system notification to user.
        
        Args:
            user_id: User to send notification to
            notification: Notification data
        """
        try:
            notification_message = {
                'notification': notification,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.sio.emit(
                'notification',
                notification_message,
                room=f"user_{user_id}"
            )
            
            logger.info(f"Sent notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
    
    def get_active_users(self) -> List[str]:
        """Get list of currently active user IDs."""
        return list(self.user_sessions.keys())
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user has active connections."""
        return user_id in self.user_sessions and len(self.user_sessions[user_id]) > 0
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_sessions)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a specific user."""
        return len(self.user_sessions.get(user_id, set()))


# Global service instance will be initialized in main.py
websocket_service: Optional[WebSocketService] = None


def initialize_websocket_service(chatbot_service: ChatbotService, auth_service: AuthService) -> WebSocketService:
    """Initialize the global WebSocket service instance."""
    global websocket_service
    websocket_service = WebSocketService(chatbot_service, auth_service)
    return websocket_service