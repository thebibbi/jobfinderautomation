"""
WebSocket Manager Service

Real-time updates and notifications via WebSockets.
"""
from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket
from datetime import datetime
import json
import asyncio
from loguru import logger
from enum import Enum


class EventType(str, Enum):
    """WebSocket event types"""
    # Job events
    JOB_CREATED = "job.created"
    JOB_ANALYZING = "job.analyzing"
    JOB_ANALYZED = "job.analyzed"
    JOB_UPDATED = "job.updated"

    # Application events
    APPLICATION_STATUS_CHANGED = "application.status_changed"
    INTERVIEW_SCHEDULED = "interview.scheduled"
    OFFER_RECEIVED = "offer.received"

    # Recommendation events
    NEW_RECOMMENDATIONS = "recommendations.new"
    RECOMMENDATION_VIEWED = "recommendation.viewed"

    # Analysis events
    SKILL_GAP_COMPLETED = "skill_gap.completed"
    COMPANY_RESEARCH_COMPLETED = "company_research.completed"

    # Follow-up events
    FOLLOW_UP_DUE = "followup.due"
    FOLLOW_UP_SENT = "followup.sent"
    RESPONSE_RECEIVED = "followup.response"

    # Learning events
    LEARNING_MILESTONE = "learning.milestone"
    SKILL_ASSESSMENT_READY = "skill.assessment_ready"

    # System events
    SYSTEM_NOTIFICATION = "system.notification"
    CACHE_CLEARED = "cache.cleared"
    ANALYTICS_UPDATED = "analytics.updated"


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events
    """

    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # User-specific connections: {user_id: {connection_id}}
        self.user_connections: Dict[str, Set[str]] = {}

        # Channel subscriptions: {channel: {connection_id}}
        self.channel_subscriptions: Dict[str, Set[str]] = {}

        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        logger.info("WebSocket Manager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        channels: Optional[List[str]] = None
    ):
        """
        Accept a new WebSocket connection

        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique connection identifier
            user_id: Optional user identifier
            channels: List of channels to subscribe to
        """
        await websocket.accept()

        # Store connection
        self.active_connections[connection_id] = websocket

        # Store metadata
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.utcnow(),
            "user_id": user_id,
            "last_ping": datetime.utcnow()
        }

        # Add to user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

        # Subscribe to channels
        if channels:
            for channel in channels:
                await self.subscribe(connection_id, channel)

        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")

        # Send welcome message
        await self.send_personal_message(
            connection_id,
            {
                "type": "system.connected",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to Job Automation System"
            }
        )

    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id in self.active_connections:
            # Remove from active connections
            del self.active_connections[connection_id]

            # Get user_id before removing metadata
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")

            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from channel subscriptions
            for channel in list(self.channel_subscriptions.keys()):
                self.channel_subscriptions[channel].discard(connection_id)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]

            # Remove metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]

            logger.info(f"WebSocket disconnected: {connection_id}")

    async def subscribe(self, connection_id: str, channel: str):
        """Subscribe connection to a channel"""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()

        self.channel_subscriptions[channel].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to {channel}")

    async def unsubscribe(self, connection_id: str, channel: str):
        """Unsubscribe connection from a channel"""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(connection_id)
            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]
            logger.debug(f"Connection {connection_id} unsubscribed from {channel}")

    async def send_personal_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """Send message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                await self.send_personal_message(connection_id, message)

    async def broadcast_to_channel(
        self,
        channel: str,
        message: Dict[str, Any]
    ):
        """Broadcast message to all subscribers of a channel"""
        if channel in self.channel_subscriptions:
            connection_ids = list(self.channel_subscriptions[channel])
            for connection_id in connection_ids:
                await self.send_personal_message(connection_id, message)

    async def broadcast_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.send_personal_message(connection_id, message)

    async def emit_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        channel: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Emit an event to relevant connections

        Args:
            event_type: Type of event
            data: Event data
            channel: Optional channel to broadcast to
            user_id: Optional user to send to
        """
        message = {
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        if user_id:
            # Send to specific user
            await self.send_to_user(user_id, message)
        elif channel:
            # Broadcast to channel
            await self.broadcast_to_channel(channel, message)
        else:
            # Broadcast to all
            await self.broadcast_all(message)

    async def ping_connections(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {
            "type": "system.ping",
            "timestamp": datetime.utcnow().isoformat()
        }

        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            try:
                await self.send_personal_message(connection_id, ping_message)

                # Update last ping time
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
            except Exception as e:
                logger.error(f"Ping failed for {connection_id}: {e}")
                self.disconnect(connection_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user"""
        if user_id in self.user_connections:
            return len(self.user_connections[user_id])
        return 0

    def get_channel_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers to a channel"""
        if channel in self.channel_subscriptions:
            return len(self.channel_subscriptions[channel])
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "unique_users": len(self.user_connections),
            "channels": len(self.channel_subscriptions),
            "channel_details": {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscriptions.items()
            }
        }


# Global WebSocket manager instance
_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """Get global WebSocket manager instance"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager


# Background task for periodic ping
async def websocket_ping_task():
    """Background task to ping connections every 30 seconds"""
    manager = get_ws_manager()
    while True:
        await asyncio.sleep(30)
        try:
            await manager.ping_connections()
        except Exception as e:
            logger.error(f"Error in ping task: {e}")


# Event broadcasting helpers

async def notify_job_analyzed(job_id: int, match_score: float, recommendation: str):
    """Notify when job analysis is complete"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.JOB_ANALYZED,
        {
            "job_id": job_id,
            "match_score": match_score,
            "recommendation": recommendation
        },
        channel="jobs"
    )


async def notify_application_status_changed(
    job_id: int,
    old_status: str,
    new_status: str
):
    """Notify when application status changes"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.APPLICATION_STATUS_CHANGED,
        {
            "job_id": job_id,
            "old_status": old_status,
            "new_status": new_status
        },
        channel="applications"
    )


async def notify_new_recommendations(count: int, top_recommendations: List[Dict]):
    """Notify about new job recommendations"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.NEW_RECOMMENDATIONS,
        {
            "count": count,
            "top_recommendations": top_recommendations
        },
        channel="recommendations"
    )


async def notify_interview_scheduled(job_id: int, interview_data: Dict):
    """Notify when interview is scheduled"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.INTERVIEW_SCHEDULED,
        {
            "job_id": job_id,
            "interview": interview_data
        },
        channel="interviews"
    )


async def notify_skill_gap_completed(job_id: int, overall_match: float):
    """Notify when skill gap analysis is complete"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.SKILL_GAP_COMPLETED,
        {
            "job_id": job_id,
            "overall_match": overall_match
        },
        channel="skills"
    )


async def notify_follow_up_due(follow_up_id: int, job_title: str, company: str):
    """Notify when follow-up is due"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.FOLLOW_UP_DUE,
        {
            "follow_up_id": follow_up_id,
            "job_title": job_title,
            "company": company
        },
        channel="followups"
    )


async def notify_system_message(message: str, severity: str = "info"):
    """Send system notification to all clients"""
    manager = get_ws_manager()
    await manager.emit_event(
        EventType.SYSTEM_NOTIFICATION,
        {
            "message": message,
            "severity": severity
        }
    )
