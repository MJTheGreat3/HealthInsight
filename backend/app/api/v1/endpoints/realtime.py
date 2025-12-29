"""
Real-time synchronization endpoints for managing data updates and WebSocket connections.

This module provides REST API endpoints for managing real-time data synchronization,
WebSocket connection status, and event subscriptions.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.decorators import require_auth
from app.services.realtime_sync import realtime_sync_service, SyncEventType
from app.services.websocket import websocket_service

router = APIRouter()


class SubscriptionRequest(BaseModel):
    """Request model for event subscriptions."""
    event_types: List[str]


class SyncRequest(BaseModel):
    """Request model for data synchronization."""
    data_types: List[str]
    force_refresh: bool = False


class ConnectionStatusResponse(BaseModel):
    """Response model for connection status."""
    user_online: bool
    connection_count: int
    subscribed_events: List[str]
    websocket_status: str


class SyncStatsResponse(BaseModel):
    """Response model for synchronization statistics."""
    total_users: int
    total_subscriptions: int
    average_subscriptions_per_user: float
    event_type_counts: Dict[str, int]
    recent_events: int


class EventHistoryResponse(BaseModel):
    """Response model for event history."""
    events: List[Dict[str, Any]]
    total_count: int


@router.get("/status", response_model=ConnectionStatusResponse)
@require_auth
async def get_connection_status(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Get real-time connection status for the current user.
    
    Returns:
        ConnectionStatusResponse: User's connection and subscription status
    """
    try:
        user_id = current_user["uid"]
        
        # Get WebSocket connection status
        user_online = websocket_service.is_user_online(user_id) if websocket_service else False
        connection_count = websocket_service.get_user_connection_count(user_id) if websocket_service else 0
        
        # Get event subscriptions
        subscribed_events = realtime_sync_service.get_user_subscriptions(user_id)
        
        return ConnectionStatusResponse(
            user_online=user_online,
            connection_count=connection_count,
            subscribed_events=subscribed_events,
            websocket_status="active" if websocket_service else "inactive"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection status: {str(e)}"
        )


@router.post("/subscribe")
@require_auth
async def subscribe_to_events(
    request: SubscriptionRequest,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Subscribe to real-time events.
    
    Args:
        request: Event subscription request
        
    Returns:
        Dict: Success message with subscription details
    """
    try:
        user_id = current_user["uid"]
        
        # Validate event types
        valid_event_types = []
        for event_type_str in request.event_types:
            try:
                event_type = SyncEventType(event_type_str)
                valid_event_types.append(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {event_type_str}"
                )
        
        # Subscribe to events
        success = await realtime_sync_service.subscribe_user_to_events(
            user_id, valid_event_types
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to subscribe to events"
            )
        
        return {
            "message": f"Successfully subscribed to {len(valid_event_types)} event types",
            "subscribed_events": [event.value for event in valid_event_types]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to subscribe to events: {str(e)}"
        )


@router.delete("/subscribe")
@require_auth
async def unsubscribe_from_events(
    request: Optional[SubscriptionRequest] = None,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Unsubscribe from real-time events.
    
    Args:
        request: Optional event unsubscription request (None = unsubscribe from all)
        
    Returns:
        Dict: Success message
    """
    try:
        user_id = current_user["uid"]
        
        event_types = None
        if request and request.event_types:
            # Validate event types
            event_types = []
            for event_type_str in request.event_types:
                try:
                    event_type = SyncEventType(event_type_str)
                    event_types.append(event_type)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid event type: {event_type_str}"
                    )
        
        # Unsubscribe from events
        success = await realtime_sync_service.unsubscribe_user_from_events(
            user_id, event_types
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unsubscribe from events"
            )
        
        message = "Successfully unsubscribed from all events" if event_types is None else f"Successfully unsubscribed from {len(event_types)} event types"
        
        return {"message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe from events: {str(e)}"
        )


@router.post("/sync")
@require_auth
async def trigger_data_sync(
    request: SyncRequest,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Trigger manual data synchronization.
    
    Args:
        request: Data synchronization request
        
    Returns:
        Dict: Success message
    """
    try:
        user_id = current_user["uid"]
        
        # Validate data types
        valid_data_types = ["reports", "metrics", "profile", "dashboard", "chat"]
        invalid_types = [dt for dt in request.data_types if dt not in valid_data_types]
        
        if invalid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data types: {invalid_types}. Valid types: {valid_data_types}"
            )
        
        # Trigger synchronization
        success = await realtime_sync_service.sync_user_data(
            user_id, request.data_types, request.force_refresh
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger data synchronization"
            )
        
        return {
            "message": f"Data synchronization triggered for: {', '.join(request.data_types)}",
            "force_refresh": request.force_refresh
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger data sync: {str(e)}"
        )


@router.get("/events", response_model=List[str])
@require_auth
async def get_available_events(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Get list of available event types for subscription.
    
    Returns:
        List[str]: Available event type names
    """
    try:
        return [event.value for event in SyncEventType]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available events: {str(e)}"
        )


@router.get("/stats", response_model=SyncStatsResponse)
@require_auth
async def get_sync_statistics(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Get real-time synchronization statistics.
    
    Returns:
        SyncStatsResponse: Synchronization statistics
    """
    try:
        stats = realtime_sync_service.get_subscription_stats()
        
        return SyncStatsResponse(
            total_users=stats["total_users"],
            total_subscriptions=stats["total_subscriptions"],
            average_subscriptions_per_user=stats["average_subscriptions_per_user"],
            event_type_counts=stats["event_type_counts"],
            recent_events=stats["recent_events"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync statistics: {str(e)}"
        )


@router.get("/history", response_model=EventHistoryResponse)
@require_auth
async def get_event_history(
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get recent synchronization event history.
    
    Args:
        limit: Maximum number of events to return
        
    Returns:
        EventHistoryResponse: Recent event history
    """
    try:
        # Limit the maximum number of events that can be requested
        limit = min(limit, 100)
        
        events = realtime_sync_service.get_recent_events(limit)
        
        # Filter events to only show user's own events for privacy
        user_id = current_user["uid"]
        user_events = [event for event in events if event.get("user_id") == user_id]
        
        return EventHistoryResponse(
            events=user_events,
            total_count=len(user_events)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event history: {str(e)}"
        )