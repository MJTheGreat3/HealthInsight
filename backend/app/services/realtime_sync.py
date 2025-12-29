"""
Real-time Synchronization Service for data change notifications.

This service provides centralized management of real-time data synchronization
across all application components, ensuring consistent data updates for all
active user sessions.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

from app.services.websocket import websocket_service

logger = logging.getLogger(__name__)


class SyncEventType(str, Enum):
    """Types of synchronization events."""
    # Report events
    REPORT_UPLOADED = "report_uploaded"
    REPORT_PROCESSING_STARTED = "report_processing_started"
    REPORT_PROCESSING_COMPLETED = "report_processing_completed"
    REPORT_PROCESSING_FAILED = "report_processing_failed"
    REPORT_ANALYSIS_COMPLETED = "report_analysis_completed"
    
    # Metrics events
    METRIC_ADDED_TO_TRACKING = "metric_added_to_tracking"
    METRIC_REMOVED_FROM_TRACKING = "metric_removed_from_tracking"
    METRICS_UPDATED = "metrics_updated"
    DASHBOARD_DATA_UPDATED = "dashboard_data_updated"
    
    # Profile events
    PROFILE_UPDATED = "profile_updated"
    BIO_DATA_UPDATED = "bio_data_updated"
    
    # Chat events
    CHAT_SESSION_STARTED = "chat_session_started"
    CHAT_MESSAGE_RECEIVED = "chat_message_received"
    
    # System events
    DATA_SYNC_REQUIRED = "data_sync_required"
    SESSION_EXPIRED = "session_expired"


class RealtimeSyncService:
    """Service for managing real-time data synchronization."""
    
    def __init__(self):
        """Initialize the real-time sync service."""
        self.active_subscriptions: Dict[str, Set[SyncEventType]] = {}  # user_id -> event_types
        self.event_history: List[Dict[str, Any]] = []  # Recent events for debugging
        self.max_history_size = 100
    
    async def subscribe_user_to_events(
        self, 
        user_id: str, 
        event_types: List[SyncEventType]
    ) -> bool:
        """
        Subscribe a user to specific event types.
        
        Args:
            user_id: User identifier
            event_types: List of event types to subscribe to
            
        Returns:
            True if subscription was successful
        """
        try:
            if user_id not in self.active_subscriptions:
                self.active_subscriptions[user_id] = set()
            
            self.active_subscriptions[user_id].update(event_types)
            
            logger.info(f"User {user_id} subscribed to {len(event_types)} event types")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id} to events: {str(e)}")
            return False
    
    async def unsubscribe_user_from_events(
        self, 
        user_id: str, 
        event_types: Optional[List[SyncEventType]] = None
    ) -> bool:
        """
        Unsubscribe a user from specific event types or all events.
        
        Args:
            user_id: User identifier
            event_types: List of event types to unsubscribe from, or None for all
            
        Returns:
            True if unsubscription was successful
        """
        try:
            if user_id not in self.active_subscriptions:
                return True
            
            if event_types is None:
                # Unsubscribe from all events
                del self.active_subscriptions[user_id]
            else:
                # Unsubscribe from specific events
                self.active_subscriptions[user_id].difference_update(event_types)
                
                # Remove user if no subscriptions left
                if not self.active_subscriptions[user_id]:
                    del self.active_subscriptions[user_id]
            
            logger.info(f"User {user_id} unsubscribed from events")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe user {user_id} from events: {str(e)}")
            return False
    
    async def broadcast_sync_event(
        self,
        event_type: SyncEventType,
        user_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Broadcast a synchronization event to subscribed users.
        
        Args:
            event_type: Type of synchronization event
            user_id: User who triggered the event
            data: Event data payload
            metadata: Optional metadata about the event
            
        Returns:
            True if broadcast was successful
        """
        try:
            # Create event record
            event_record = {
                "event_type": event_type.value,
                "user_id": user_id,
                "data": data,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "broadcast_count": 0
            }
            
            # Add to event history
            self._add_to_event_history(event_record)
            
            # Check if user is subscribed to this event type
            if (user_id in self.active_subscriptions and 
                event_type in self.active_subscriptions[user_id]):
                
                # Broadcast via WebSocket service
                if websocket_service:
                    await websocket_service.broadcast_data_update(
                        user_id,
                        event_type.value,
                        {
                            "data": data,
                            "metadata": metadata or {},
                            "timestamp": event_record["timestamp"]
                        }
                    )
                    event_record["broadcast_count"] = 1
                    
                    logger.info(f"Broadcasted {event_type.value} event to user {user_id}")
                else:
                    logger.warning("WebSocket service not available for broadcasting")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast sync event {event_type.value}: {str(e)}")
            return False
    
    async def broadcast_to_multiple_users(
        self,
        event_type: SyncEventType,
        user_ids: List[str],
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Broadcast a synchronization event to multiple users.
        
        Args:
            event_type: Type of synchronization event
            user_ids: List of user IDs to broadcast to
            data: Event data payload
            metadata: Optional metadata about the event
            
        Returns:
            Number of successful broadcasts
        """
        successful_broadcasts = 0
        
        for user_id in user_ids:
            success = await self.broadcast_sync_event(
                event_type, user_id, data, metadata
            )
            if success:
                successful_broadcasts += 1
        
        logger.info(f"Broadcasted {event_type.value} to {successful_broadcasts}/{len(user_ids)} users")
        return successful_broadcasts
    
    async def sync_user_data(
        self,
        user_id: str,
        data_types: List[str],
        force_refresh: bool = False
    ) -> bool:
        """
        Trigger data synchronization for a specific user.
        
        Args:
            user_id: User identifier
            data_types: Types of data to synchronize (reports, metrics, profile, etc.)
            force_refresh: Whether to force a complete data refresh
            
        Returns:
            True if synchronization was triggered successfully
        """
        try:
            sync_data = {
                "data_types": data_types,
                "force_refresh": force_refresh,
                "sync_requested_at": datetime.utcnow().isoformat()
            }
            
            await self.broadcast_sync_event(
                SyncEventType.DATA_SYNC_REQUIRED,
                user_id,
                sync_data,
                {"trigger": "manual_sync"}
            )
            
            logger.info(f"Triggered data sync for user {user_id}: {data_types}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger data sync for user {user_id}: {str(e)}")
            return False
    
    async def handle_session_change(
        self,
        user_id: str,
        session_event: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """
        Handle user session changes (login, logout, timeout).
        
        Args:
            user_id: User identifier
            session_event: Type of session event (login, logout, timeout)
            session_data: Session-related data
            
        Returns:
            True if session change was handled successfully
        """
        try:
            if session_event == "logout" or session_event == "timeout":
                # Clean up subscriptions for logged out users
                await self.unsubscribe_user_from_events(user_id)
                
                # Broadcast session expired event if timeout
                if session_event == "timeout":
                    await self.broadcast_sync_event(
                        SyncEventType.SESSION_EXPIRED,
                        user_id,
                        session_data,
                        {"reason": "timeout"}
                    )
            
            elif session_event == "login":
                # Auto-subscribe to common events on login
                common_events = [
                    SyncEventType.REPORT_PROCESSING_COMPLETED,
                    SyncEventType.METRICS_UPDATED,
                    SyncEventType.DASHBOARD_DATA_UPDATED,
                    SyncEventType.PROFILE_UPDATED
                ]
                await self.subscribe_user_to_events(user_id, common_events)
            
            logger.info(f"Handled session {session_event} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle session change for user {user_id}: {str(e)}")
            return False
    
    def get_user_subscriptions(self, user_id: str) -> List[str]:
        """Get list of event types a user is subscribed to."""
        if user_id in self.active_subscriptions:
            return [event.value for event in self.active_subscriptions[user_id]]
        return []
    
    def get_active_users(self) -> List[str]:
        """Get list of users with active subscriptions."""
        return list(self.active_subscriptions.keys())
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get statistics about active subscriptions."""
        total_users = len(self.active_subscriptions)
        total_subscriptions = sum(len(events) for events in self.active_subscriptions.values())
        
        event_counts = {}
        for events in self.active_subscriptions.values():
            for event in events:
                event_counts[event.value] = event_counts.get(event.value, 0) + 1
        
        return {
            "total_users": total_users,
            "total_subscriptions": total_subscriptions,
            "average_subscriptions_per_user": total_subscriptions / total_users if total_users > 0 else 0,
            "event_type_counts": event_counts,
            "recent_events": len(self.event_history)
        }
    
    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent synchronization events."""
        return self.event_history[-limit:] if self.event_history else []
    
    def _add_to_event_history(self, event_record: Dict[str, Any]) -> None:
        """Add event to history with size limit."""
        self.event_history.append(event_record)
        
        # Maintain history size limit
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]


# Global service instance
realtime_sync_service = RealtimeSyncService()