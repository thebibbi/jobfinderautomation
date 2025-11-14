"""
WebSocket API

Real-time event streaming endpoints.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, List
from loguru import logger
import uuid
import asyncio

from ..services.websocket_service import get_ws_manager, EventType


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    channels: Optional[str] = Query(None)  # Comma-separated list
):
    """
    WebSocket endpoint for real-time updates

    Query params:
        user_id: Optional user identifier
        channels: Comma-separated list of channels to subscribe to
                 (e.g., "jobs,applications,recommendations")

    Available channels:
        - jobs: Job creation, analysis, updates
        - applications: Application status changes, interviews
        - recommendations: New recommendations
        - skills: Skill gap analysis, learning progress
        - followups: Follow-up reminders and responses
        - interviews: Interview scheduling and updates
        - system: System notifications

    Message format:
        {
            "type": "event.type",
            "data": {...},
            "timestamp": "2024-01-01T12:00:00"
        }

    Client can send:
        {
            "action": "subscribe",
            "channel": "jobs"
        }
        {
            "action": "unsubscribe",
            "channel": "jobs"
        }
        {
            "action": "ping"
        }
    """
    manager = get_ws_manager()
    connection_id = str(uuid.uuid4())

    # Parse channels
    channel_list = []
    if channels:
        channel_list = [c.strip() for c in channels.split(",")]

    try:
        # Connect
        await manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            channels=channel_list
        )

        # Message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                # Handle client messages
                action = data.get("action")

                if action == "subscribe":
                    channel = data.get("channel")
                    if channel:
                        await manager.subscribe(connection_id, channel)
                        await manager.send_personal_message(
                            connection_id,
                            {
                                "type": "system.subscribed",
                                "channel": channel,
                                "message": f"Subscribed to {channel}"
                            }
                        )

                elif action == "unsubscribe":
                    channel = data.get("channel")
                    if channel:
                        await manager.unsubscribe(connection_id, channel)
                        await manager.send_personal_message(
                            connection_id,
                            {
                                "type": "system.unsubscribed",
                                "channel": channel,
                                "message": f"Unsubscribed from {channel}"
                            }
                        )

                elif action == "ping":
                    await manager.send_personal_message(
                        connection_id,
                        {
                            "type": "system.pong",
                            "message": "pong"
                        }
                    )

                elif action == "get_stats":
                    stats = manager.get_stats()
                    await manager.send_personal_message(
                        connection_id,
                        {
                            "type": "system.stats",
                            "data": stats
                        }
                    )

                else:
                    await manager.send_personal_message(
                        connection_id,
                        {
                            "type": "system.error",
                            "message": f"Unknown action: {action}"
                        }
                    )

            except WebSocketDisconnect:
                logger.info(f"Client {connection_id} disconnected")
                break

            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                await manager.send_personal_message(
                    connection_id,
                    {
                        "type": "system.error",
                        "message": str(e)
                    }
                )

    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")

    finally:
        manager.disconnect(connection_id)


@router.get("/connections")
async def get_connection_stats():
    """Get WebSocket connection statistics"""
    manager = get_ws_manager()
    return manager.get_stats()


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    channel: Optional[str] = None,
    severity: str = "info"
):
    """
    Broadcast a message to connected clients (admin endpoint)

    Args:
        message: Message to broadcast
        channel: Optional channel to broadcast to
        severity: Message severity (info, warning, error)
    """
    try:
        manager = get_ws_manager()

        event_data = {
            "message": message,
            "severity": severity
        }

        await manager.emit_event(
            EventType.SYSTEM_NOTIFICATION,
            event_data,
            channel=channel
        )

        return {
            "status": "success",
            "message": "Message broadcasted",
            "recipients": manager.get_channel_subscriber_count(channel) if channel else manager.get_connection_count()
        }

    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
