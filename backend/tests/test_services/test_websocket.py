"""
Tests for WebSocket Service
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.services.websocket_service import (
    WebSocketManager, EventType, get_ws_manager,
    notify_job_analyzed, notify_application_status_changed
)


class TestWebSocketManager:
    """Test WebSocket manager functionality"""

    @pytest.fixture
    def manager(self):
        """Create fresh WebSocket manager for each test"""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, manager):
        """Should connect and disconnect WebSockets"""
        mock_ws = AsyncMock()

        # Connect
        await manager.connect(
            websocket=mock_ws,
            connection_id="conn-1",
            user_id="user-1"
        )

        assert manager.get_connection_count() == 1
        assert manager.get_user_connection_count("user-1") == 1
        mock_ws.accept.assert_called_once()

        # Disconnect
        manager.disconnect("conn-1")

        assert manager.get_connection_count() == 0
        assert manager.get_user_connection_count("user-1") == 0

    @pytest.mark.asyncio
    async def test_connect_with_channels(self, manager):
        """Should subscribe to channels on connect"""
        mock_ws = AsyncMock()

        await manager.connect(
            websocket=mock_ws,
            connection_id="conn-1",
            channels=["jobs", "applications"]
        )

        assert manager.get_channel_subscriber_count("jobs") == 1
        assert manager.get_channel_subscriber_count("applications") == 1

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, manager):
        """Should handle channel subscriptions"""
        mock_ws = AsyncMock()

        await manager.connect(
            websocket=mock_ws,
            connection_id="conn-1"
        )

        # Subscribe
        await manager.subscribe("conn-1", "jobs")
        assert manager.get_channel_subscriber_count("jobs") == 1

        # Unsubscribe
        await manager.unsubscribe("conn-1", "jobs")
        assert manager.get_channel_subscriber_count("jobs") == 0

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager):
        """Should send message to specific connection"""
        mock_ws = AsyncMock()

        await manager.connect(
            websocket=mock_ws,
            connection_id="conn-1"
        )

        # Send message
        await manager.send_personal_message(
            "conn-1",
            {"type": "test", "data": "hello"}
        )

        # Verify message sent (called twice: welcome + test message)
        assert mock_ws.send_json.call_count == 2
        last_call = mock_ws.send_json.call_args[0][0]
        assert last_call["type"] == "test"
        assert last_call["data"] == "hello"

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager):
        """Should send message to all user connections"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # User with 2 connections
        await manager.connect(
            websocket=mock_ws1,
            connection_id="conn-1",
            user_id="user-1"
        )
        await manager.connect(
            websocket=mock_ws2,
            connection_id="conn-2",
            user_id="user-1"
        )

        # Send to user
        await manager.send_to_user(
            "user-1",
            {"type": "test", "data": "hello"}
        )

        # Both connections should receive (plus welcome messages)
        assert mock_ws1.send_json.call_count == 2
        assert mock_ws2.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, manager):
        """Should broadcast to channel subscribers"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()

        # 2 connections subscribe to "jobs", 1 to "applications"
        await manager.connect(mock_ws1, "conn-1", channels=["jobs"])
        await manager.connect(mock_ws2, "conn-2", channels=["jobs"])
        await manager.connect(mock_ws3, "conn-3", channels=["applications"])

        # Broadcast to "jobs"
        await manager.broadcast_to_channel(
            "jobs",
            {"type": "test", "data": "hello"}
        )

        # Only jobs subscribers should receive (plus welcome messages)
        assert mock_ws1.send_json.call_count == 2
        assert mock_ws2.send_json.call_count == 2
        assert mock_ws3.send_json.call_count == 1  # Only welcome

    @pytest.mark.asyncio
    async def test_broadcast_all(self, manager):
        """Should broadcast to all connections"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, "conn-1")
        await manager.connect(mock_ws2, "conn-2")

        await manager.broadcast_all({"type": "test", "data": "hello"})

        # All should receive (plus welcome messages)
        assert mock_ws1.send_json.call_count == 2
        assert mock_ws2.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_emit_event(self, manager):
        """Should emit events with proper format"""
        mock_ws = AsyncMock()

        await manager.connect(mock_ws, "conn-1", channels=["jobs"])

        await manager.emit_event(
            EventType.JOB_ANALYZED,
            {"job_id": 123, "score": 85},
            channel="jobs"
        )

        # Should receive formatted event (plus welcome)
        assert mock_ws.send_json.call_count == 2
        last_call = mock_ws.send_json.call_args[0][0]
        assert last_call["type"] == "job.analyzed"
        assert last_call["data"]["job_id"] == 123
        assert "timestamp" in last_call

    @pytest.mark.asyncio
    async def test_ping_connections(self, manager):
        """Should ping all active connections"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, "conn-1")
        await manager.connect(mock_ws2, "conn-2")

        await manager.ping_connections()

        # Each should receive ping (plus welcome)
        assert mock_ws1.send_json.call_count == 2
        assert mock_ws2.send_json.call_count == 2

        # Last call should be ping
        last_call = mock_ws1.send_json.call_args[0][0]
        assert last_call["type"] == "system.ping"

    @pytest.mark.asyncio
    async def test_multiple_users(self, manager):
        """Should handle multiple users"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, "conn-1", user_id="user-1")
        await manager.connect(mock_ws2, "conn-2", user_id="user-2")

        assert manager.get_connection_count() == 2
        assert manager.get_stats()["unique_users"] == 2

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, manager):
        """Should handle connection errors gracefully"""
        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection error")

        await manager.connect(mock_ws, "conn-1")

        # This should not raise
        await manager.send_personal_message(
            "conn-1",
            {"type": "test"}
        )

        # Connection should be disconnected on error
        assert manager.get_connection_count() == 0

    def test_get_stats(self, manager):
        """Should return connection statistics"""
        stats = manager.get_stats()

        assert "total_connections" in stats
        assert "unique_users" in stats
        assert "channels" in stats
        assert "channel_details" in stats


class TestEventBroadcasting:
    """Test event broadcasting helpers"""

    @pytest.mark.asyncio
    async def test_notify_job_analyzed(self):
        """Should notify when job is analyzed"""
        with patch('app.services.websocket_service.get_ws_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            await notify_job_analyzed(
                job_id=123,
                match_score=85.5,
                recommendation="apply_now"
            )

            mock_manager.emit_event.assert_called_once()
            call_args = mock_manager.emit_event.call_args

            assert call_args[0][0] == EventType.JOB_ANALYZED
            assert call_args[0][1]["job_id"] == 123
            assert call_args[0][1]["match_score"] == 85.5
            assert call_args[1]["channel"] == "jobs"

    @pytest.mark.asyncio
    async def test_notify_application_status_changed(self):
        """Should notify when application status changes"""
        with patch('app.services.websocket_service.get_ws_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            await notify_application_status_changed(
                job_id=123,
                old_status="applied",
                new_status="interviewing"
            )

            mock_manager.emit_event.assert_called_once()
            call_args = mock_manager.emit_event.call_args

            assert call_args[0][0] == EventType.APPLICATION_STATUS_CHANGED
            assert call_args[0][1]["old_status"] == "applied"
            assert call_args[0][1]["new_status"] == "interviewing"
            assert call_args[1]["channel"] == "applications"


class TestEventTypes:
    """Test event type definitions"""

    def test_all_event_types_defined(self):
        """Should have all expected event types"""
        expected_events = [
            "JOB_CREATED",
            "JOB_ANALYZING",
            "JOB_ANALYZED",
            "APPLICATION_STATUS_CHANGED",
            "NEW_RECOMMENDATIONS",
            "SKILL_GAP_COMPLETED",
            "FOLLOW_UP_DUE",
            "SYSTEM_NOTIFICATION"
        ]

        for event in expected_events:
            assert hasattr(EventType, event)

    def test_event_type_values(self):
        """Should have correct event type values"""
        assert EventType.JOB_ANALYZED.value == "job.analyzed"
        assert EventType.APPLICATION_STATUS_CHANGED.value == "application.status_changed"
        assert EventType.NEW_RECOMMENDATIONS.value == "recommendations.new"
