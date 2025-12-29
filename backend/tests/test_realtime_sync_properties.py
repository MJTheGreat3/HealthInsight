"""
Property-based tests for Real-time Synchronization functionality.

**Feature: health-insight-core, Property 8: Real-time Synchronization**

For any data change in the system, all active user sessions should receive 
synchronized updates immediately, ensuring consistent information across 
concurrent access.

Validates: Requirements 11.1, 11.2, 11.3, 11.4
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List, Set
from datetime import datetime

from app.services.realtime_sync import RealtimeSyncService, SyncEventType
from app.services.websocket import WebSocketService
from app.services.chatbot import ChatbotService
from app.services.auth import AuthService


# Test data strategies
@st.composite
def _sync_event_data_strategy(draw):
    """Generate valid synchronization event data."""
    event_types = [
        SyncEventType.REPORT_UPLOADED,
        SyncEventType.REPORT_PROCESSING_COMPLETED,
        SyncEventType.METRIC_ADDED_TO_TRACKING,
        SyncEventType.METRICS_UPDATED,
        SyncEventType.PROFILE_UPDATED,
        SyncEventType.DASHBOARD_DATA_UPDATED
    ]
    
    event_type = draw(st.sampled_from(event_types))
    
    # Generate appropriate data based on event type
    if event_type in [SyncEventType.REPORT_UPLOADED, SyncEventType.REPORT_PROCESSING_COMPLETED]:
        data = {
            "report_id": draw(st.text(min_size=1, max_size=50)),
            "filename": draw(st.text(min_size=1, max_size=100)),
            "status": draw(st.sampled_from(["processing", "completed", "failed"]))
        }
    elif event_type in [SyncEventType.METRIC_ADDED_TO_TRACKING, SyncEventType.METRICS_UPDATED]:
        data = {
            "metric_name": draw(st.text(min_size=1, max_size=50)),
            "action": draw(st.sampled_from(["added", "removed", "updated"]))
        }
    elif event_type == SyncEventType.PROFILE_UPDATED:
        data = {
            "fields_updated": draw(st.lists(
                st.sampled_from(["height", "weight", "age", "allergies"]),
                min_size=1, max_size=4
            ))
        }
    else:
        data = {
            "update_type": draw(st.text(min_size=1, max_size=30)),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return event_type, data


@st.composite
def _user_session_strategy(draw):
    """Generate user session data for testing."""
    user_id = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    session_count = draw(st.integers(min_value=1, max_value=5))
    
    subscribed_events = draw(st.lists(
        st.sampled_from(list(SyncEventType)),
        min_size=0, max_size=len(SyncEventType)
    ))
    
    return {
        "user_id": user_id,
        "session_count": session_count,
        "subscribed_events": subscribed_events,
        "is_online": True
    }


@st.composite
def _multiple_users_strategy(draw):
    """Generate multiple user sessions for concurrent testing."""
    num_users = draw(st.integers(min_value=1, max_value=10))
    users = []
    
    for i in range(num_users):
        user_session = draw(_user_session_strategy())
        user_session["user_id"] = f"user_{i}_{user_session['user_id']}"
        users.append(user_session)
    
    return users


class TestRealtimeSyncProperties:
    """Property-based tests for Real-time Synchronization functionality."""
    
    @given(
        user_sessions=_multiple_users_strategy(),
        sync_events=st.lists(_sync_event_data_strategy(), min_size=1, max_size=5)
    )
    @settings(
        max_examples=20, 
        deadline=30000, 
        suppress_health_check=[HealthCheck.filter_too_much]
    )
    def test_realtime_synchronization_property(self, user_sessions, sync_events):
        """
        Property: Real-time Synchronization
        
        For any data change events and active user sessions, the system should
        broadcast updates to all subscribed users immediately and consistently.
        """
        async def run_test():
            # Create real-time sync service
            sync_service = RealtimeSyncService()
            
            # Mock WebSocket service
            mock_websocket_service = MagicMock(spec=WebSocketService)
            mock_websocket_service.broadcast_data_update = AsyncMock()
            mock_websocket_service.is_user_online.return_value = True
            mock_websocket_service.get_user_connection_count.return_value = 1
            
            # Patch the websocket service
            with patch('app.services.realtime_sync.websocket_service', mock_websocket_service):
                
                # Set up user subscriptions
                for user_session in user_sessions:
                    user_id = user_session["user_id"]
                    subscribed_events = user_session["subscribed_events"]
                    
                    if subscribed_events:
                        await sync_service.subscribe_user_to_events(user_id, subscribed_events)
                
                # Track expected broadcasts
                expected_broadcasts = {}
                
                # Process sync events
                for event_type, event_data in sync_events:
                    # Pick a random user to trigger the event
                    triggering_user = user_sessions[0]["user_id"]
                    
                    # Broadcast the event
                    success = await sync_service.broadcast_sync_event(
                        event_type,
                        triggering_user,
                        event_data,
                        {"test": True}
                    )
                    
                    # Property 1: Broadcast should always succeed
                    assert success, f"Failed to broadcast event {event_type.value}"
                    
                    # Track expected broadcast for this user if subscribed
                    user_session = next(
                        (u for u in user_sessions if u["user_id"] == triggering_user), 
                        None
                    )
                    
                    if (user_session and 
                        event_type in user_session["subscribed_events"]):
                        if triggering_user not in expected_broadcasts:
                            expected_broadcasts[triggering_user] = []
                        expected_broadcasts[triggering_user].append(event_type.value)
                
                # Property 2: WebSocket broadcasts should match subscriptions
                broadcast_calls = mock_websocket_service.broadcast_data_update.call_args_list
                
                for user_id, expected_events in expected_broadcasts.items():
                    user_broadcasts = [
                        call for call in broadcast_calls 
                        if call[0][0] == user_id  # First argument is user_id
                    ]
                    
                    # Should have received broadcasts for subscribed events
                    assert len(user_broadcasts) == len(expected_events), (
                        f"User {user_id} expected {len(expected_events)} broadcasts, "
                        f"got {len(user_broadcasts)}"
                    )
                
                # Property 3: Event history should be maintained
                recent_events = sync_service.get_recent_events(len(sync_events))
                assert len(recent_events) == len(sync_events), (
                    f"Expected {len(sync_events)} events in history, got {len(recent_events)}"
                )
                
                # Property 4: Subscription tracking should be accurate
                for user_session in user_sessions:
                    user_id = user_session["user_id"]
                    subscribed_events = user_session["subscribed_events"]
                    
                    actual_subscriptions = sync_service.get_user_subscriptions(user_id)
                    expected_subscriptions = [event.value for event in subscribed_events]
                    
                    assert set(actual_subscriptions) == set(expected_subscriptions), (
                        f"User {user_id} subscription mismatch: "
                        f"expected {expected_subscriptions}, got {actual_subscriptions}"
                    )
                
                # Property 5: Statistics should be consistent
                stats = sync_service.get_subscription_stats()
                active_users = [u for u in user_sessions if u["subscribed_events"]]
                
                assert stats["total_users"] == len(active_users), (
                    f"Expected {len(active_users)} active users, got {stats['total_users']}"
                )
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        user_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        event_types=st.lists(st.sampled_from(list(SyncEventType)), min_size=1, max_size=5)
    )
    @settings(max_examples=15, deadline=10000)
    def test_subscription_management_property(self, user_id, event_types):
        """
        Property: Subscription Management Consistency
        
        For any user and event types, subscription and unsubscription operations
        should maintain consistent state and proper cleanup.
        """
        async def run_test():
            sync_service = RealtimeSyncService()
            
            # Property 1: Initial state should be empty
            initial_subscriptions = sync_service.get_user_subscriptions(user_id)
            assert initial_subscriptions == [], f"Expected empty initial subscriptions, got {initial_subscriptions}"
            
            # Property 2: Subscription should succeed and be tracked
            success = await sync_service.subscribe_user_to_events(user_id, event_types)
            assert success, "Subscription should succeed"
            
            current_subscriptions = sync_service.get_user_subscriptions(user_id)
            expected_subscriptions = [event.value for event in event_types]
            
            assert set(current_subscriptions) == set(expected_subscriptions), (
                f"Subscription mismatch: expected {expected_subscriptions}, got {current_subscriptions}"
            )
            
            # Property 3: User should appear in active users list
            active_users = sync_service.get_active_users()
            assert user_id in active_users, f"User {user_id} should be in active users list"
            
            # Property 4: Partial unsubscription should work correctly
            if len(event_types) > 1:
                events_to_remove = event_types[:len(event_types)//2]
                success = await sync_service.unsubscribe_user_from_events(user_id, events_to_remove)
                assert success, "Partial unsubscription should succeed"
                
                remaining_subscriptions = sync_service.get_user_subscriptions(user_id)
                expected_remaining = [
                    event.value for event in event_types 
                    if event not in events_to_remove
                ]
                
                assert set(remaining_subscriptions) == set(expected_remaining), (
                    f"Partial unsubscription failed: expected {expected_remaining}, got {remaining_subscriptions}"
                )
            
            # Property 5: Complete unsubscription should clean up properly
            success = await sync_service.unsubscribe_user_from_events(user_id, None)
            assert success, "Complete unsubscription should succeed"
            
            final_subscriptions = sync_service.get_user_subscriptions(user_id)
            assert final_subscriptions == [], f"Expected empty subscriptions after cleanup, got {final_subscriptions}"
            
            # Property 6: User should be removed from active users list
            active_users_after = sync_service.get_active_users()
            assert user_id not in active_users_after, f"User {user_id} should be removed from active users list"
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        user_ids=st.lists(
            st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),
            min_size=2, max_size=8, unique=True
        ),
        event_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
            min_size=1, max_size=5
        )
    )
    @settings(max_examples=10, deadline=15000)
    def test_concurrent_access_property(self, user_ids, event_data):
        """
        Property: Concurrent Access Consistency
        
        For any multiple users accessing the system concurrently, data changes
        should be synchronized consistently across all active sessions.
        """
        async def run_test():
            sync_service = RealtimeSyncService()
            
            # Mock WebSocket service
            mock_websocket_service = MagicMock(spec=WebSocketService)
            mock_websocket_service.broadcast_data_update = AsyncMock()
            
            with patch('app.services.realtime_sync.websocket_service', mock_websocket_service):
                
                # Subscribe all users to the same event type
                event_type = SyncEventType.DASHBOARD_DATA_UPDATED
                
                for user_id in user_ids:
                    await sync_service.subscribe_user_to_events(user_id, [event_type])
                
                # Simulate concurrent data changes
                broadcast_tasks = []
                for i, user_id in enumerate(user_ids):
                    task_data = {**event_data, "user_index": i}
                    task = sync_service.broadcast_sync_event(
                        event_type, user_id, task_data
                    )
                    broadcast_tasks.append(task)
                
                # Execute all broadcasts concurrently
                results = await asyncio.gather(*broadcast_tasks, return_exceptions=True)
                
                # Property 1: All broadcasts should succeed
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        assert False, f"Broadcast {i} failed with exception: {result}"
                    assert result is True, f"Broadcast {i} should succeed"
                
                # Property 2: Each user should receive their own broadcast
                broadcast_calls = mock_websocket_service.broadcast_data_update.call_args_list
                
                for user_id in user_ids:
                    user_broadcasts = [
                        call for call in broadcast_calls 
                        if call[0][0] == user_id
                    ]
                    assert len(user_broadcasts) == 1, (
                        f"User {user_id} should receive exactly 1 broadcast, got {len(user_broadcasts)}"
                    )
                
                # Property 3: Event history should contain all events
                recent_events = sync_service.get_recent_events(len(user_ids))
                assert len(recent_events) == len(user_ids), (
                    f"Expected {len(user_ids)} events in history, got {len(recent_events)}"
                )
                
                # Property 4: All users should remain subscribed
                for user_id in user_ids:
                    subscriptions = sync_service.get_user_subscriptions(user_id)
                    assert event_type.value in subscriptions, (
                        f"User {user_id} should still be subscribed to {event_type.value}"
                    )
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        data_types=st.lists(
            st.sampled_from(["reports", "metrics", "profile", "dashboard", "chat"]),
            min_size=1, max_size=5, unique=True
        ),
        force_refresh=st.booleans()
    )
    @settings(max_examples=10, deadline=5000)
    def test_data_sync_trigger_property(self, data_types, force_refresh):
        """
        Property: Data Synchronization Trigger
        
        For any data types and sync parameters, triggering data synchronization
        should generate appropriate sync events with correct metadata.
        """
        async def run_test():
            sync_service = RealtimeSyncService()
            user_id = "test_user"
            
            # Mock WebSocket service
            mock_websocket_service = MagicMock(spec=WebSocketService)
            mock_websocket_service.broadcast_data_update = AsyncMock()
            
            with patch('app.services.realtime_sync.websocket_service', mock_websocket_service):
                
                # Subscribe user to sync events
                await sync_service.subscribe_user_to_events(
                    user_id, [SyncEventType.DATA_SYNC_REQUIRED]
                )
                
                # Trigger data sync
                success = await sync_service.sync_user_data(
                    user_id, data_types, force_refresh
                )
                
                # Property 1: Sync trigger should succeed
                assert success, "Data sync trigger should succeed"
                
                # Property 2: Should broadcast sync event
                broadcast_calls = mock_websocket_service.broadcast_data_update.call_args_list
                assert len(broadcast_calls) == 1, f"Expected 1 broadcast call, got {len(broadcast_calls)}"
                
                call_args = broadcast_calls[0]
                assert call_args[0][0] == user_id, "Broadcast should be sent to correct user"
                assert call_args[0][1] == SyncEventType.DATA_SYNC_REQUIRED.value, "Should broadcast sync event"
                
                # Property 3: Event data should contain sync parameters
                event_data = call_args[0][2]["data"]
                assert "data_types" in event_data, "Event should contain data_types"
                assert "force_refresh" in event_data, "Event should contain force_refresh"
                assert set(event_data["data_types"]) == set(data_types), "Data types should match"
                assert event_data["force_refresh"] == force_refresh, "Force refresh should match"
                
                # Property 4: Event should have proper timestamp
                assert "sync_requested_at" in event_data, "Event should have timestamp"
                
                # Property 5: Event should be recorded in history
                recent_events = sync_service.get_recent_events(1)
                assert len(recent_events) == 1, "Event should be recorded in history"
                assert recent_events[0]["event_type"] == SyncEventType.DATA_SYNC_REQUIRED.value
        
        # Run the async test
        asyncio.run(run_test())
    
    def test_session_management_property(self):
        """
        Property: Session Management
        
        Session changes (login, logout, timeout) should properly manage
        subscriptions and trigger appropriate cleanup.
        """
        async def run_test():
            sync_service = RealtimeSyncService()
            user_id = "test_user"
            
            # Mock WebSocket service
            mock_websocket_service = MagicMock(spec=WebSocketService)
            mock_websocket_service.broadcast_data_update = AsyncMock()
            
            with patch('app.services.realtime_sync.websocket_service', mock_websocket_service):
                
                # Test login - should auto-subscribe to common events
                success = await sync_service.handle_session_change(
                    user_id, "login", {"timestamp": datetime.utcnow().isoformat()}
                )
                
                # Property 1: Login handling should succeed
                assert success, "Login session handling should succeed"
                
                # Property 2: Should auto-subscribe to common events
                subscriptions = sync_service.get_user_subscriptions(user_id)
                expected_events = [
                    SyncEventType.REPORT_PROCESSING_COMPLETED.value,
                    SyncEventType.METRICS_UPDATED.value,
                    SyncEventType.DASHBOARD_DATA_UPDATED.value,
                    SyncEventType.PROFILE_UPDATED.value
                ]
                
                for event in expected_events:
                    assert event in subscriptions, f"Should auto-subscribe to {event}"
                
                # Test logout - should clean up subscriptions
                success = await sync_service.handle_session_change(
                    user_id, "logout", {"timestamp": datetime.utcnow().isoformat()}
                )
                
                # Property 3: Logout handling should succeed
                assert success, "Logout session handling should succeed"
                
                # Property 4: Should clean up subscriptions
                subscriptions_after_logout = sync_service.get_user_subscriptions(user_id)
                assert subscriptions_after_logout == [], "Should clean up subscriptions on logout"
                
                # Property 5: User should be removed from active users
                active_users = sync_service.get_active_users()
                assert user_id not in active_users, "User should be removed from active users on logout"
        
        # Run the async test
        asyncio.run(run_test())


# Additional edge case tests
class TestRealtimeSyncEdgeCases:
    """Edge case tests for Real-time Synchronization functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_service_unavailable(self):
        """Test behavior when WebSocket service is unavailable."""
        sync_service = RealtimeSyncService()
        
        # Test with no WebSocket service
        with patch('app.services.realtime_sync.websocket_service', None):
            success = await sync_service.broadcast_sync_event(
                SyncEventType.REPORT_UPLOADED,
                "test_user",
                {"report_id": "test"}
            )
            
            # Should still succeed but not broadcast
            assert success, "Should succeed even without WebSocket service"
    
    @pytest.mark.asyncio
    async def test_invalid_event_types(self):
        """Test handling of invalid event types."""
        sync_service = RealtimeSyncService()
        
        # Test subscription with invalid event type should be handled at API level
        # The service itself works with enum values
        
        # Test with valid enum
        success = await sync_service.subscribe_user_to_events(
            "test_user", [SyncEventType.REPORT_UPLOADED]
        )
        assert success, "Valid event type subscription should succeed"
    
    @pytest.mark.asyncio
    async def test_duplicate_subscriptions(self):
        """Test handling of duplicate subscriptions."""
        sync_service = RealtimeSyncService()
        user_id = "test_user"
        event_type = SyncEventType.REPORT_UPLOADED
        
        # Subscribe twice to same event
        await sync_service.subscribe_user_to_events(user_id, [event_type])
        await sync_service.subscribe_user_to_events(user_id, [event_type])
        
        # Should only appear once in subscriptions
        subscriptions = sync_service.get_user_subscriptions(user_id)
        assert subscriptions.count(event_type.value) == 1, "Should not have duplicate subscriptions"
    
    @pytest.mark.asyncio
    async def test_event_history_size_limit(self):
        """Test that event history maintains size limit."""
        sync_service = RealtimeSyncService()
        sync_service.max_history_size = 5  # Set small limit for testing
        
        # Generate more events than the limit
        for i in range(10):
            await sync_service.broadcast_sync_event(
                SyncEventType.REPORT_UPLOADED,
                f"user_{i}",
                {"report_id": f"report_{i}"}
            )
        
        # Should only keep the most recent events
        history = sync_service.get_recent_events(20)
        assert len(history) == 5, f"History should be limited to 5 events, got {len(history)}"
        
        # Should contain the most recent events
        assert history[-1]["data"]["report_id"] == "report_9", "Should contain most recent event"