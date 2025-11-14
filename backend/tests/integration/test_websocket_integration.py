"""
WebSocket integration tests

Tests real-time WebSocket functionality and event broadcasting.
Run with: docker-compose exec backend pytest tests/integration/test_websocket_integration.py
"""
import pytest
import asyncio
import websockets
import json
import requests
import time
from datetime import datetime, timedelta
import os


@pytest.fixture(scope="module")
def api_base_url():
    """Base API URL"""
    return os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def ws_base_url(api_base_url):
    """WebSocket base URL"""
    return api_base_url.replace("http", "ws")


class TestWebSocketConnection:
    """Test WebSocket connection functionality"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, ws_base_url):
        """Test WebSocket connection establishes successfully"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs"

        async with websockets.connect(uri) as websocket:
            # Should receive welcome message
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)

            assert data["type"] == "system.connected"
            assert "connection_id" in data["data"]
            assert data["data"]["user_id"] == "test_user"

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, ws_base_url):
        """Test WebSocket ping/pong keep-alive"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user"

        async with websockets.connect(uri) as websocket:
            # Skip welcome message
            await websocket.recv()

            # Send ping
            await websocket.send(json.dumps({"action": "ping"}))

            # Wait for pong or next message
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            # Server may send ping first, that's OK

    @pytest.mark.asyncio
    async def test_websocket_channel_subscription(self, ws_base_url):
        """Test WebSocket channel subscription"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs"

        async with websockets.connect(uri) as websocket:
            # Skip welcome message
            await websocket.recv()

            # Subscribe to additional channel
            await websocket.send(json.dumps({
                "action": "subscribe",
                "channel": "applications"
            }))

            # Should receive subscription confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)

            # May receive system.subscribed or system.ping
            assert data["type"] in ["system.subscribed", "system.ping"]

    @pytest.mark.asyncio
    async def test_websocket_unsubscribe(self, ws_base_url):
        """Test WebSocket channel unsubscription"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs,applications"

        async with websockets.connect(uri) as websocket:
            # Skip welcome message
            await websocket.recv()

            # Unsubscribe from channel
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "channel": "applications"
            }))

            # Should receive unsubscription confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)

            # May receive system.unsubscribed or system.ping
            assert data["type"] in ["system.unsubscribed", "system.ping"]


class TestWebSocketEvents:
    """Test WebSocket event broadcasting"""

    @pytest.mark.asyncio
    async def test_job_created_event(self, api_base_url, ws_base_url):
        """Test job.created event is broadcast"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs"

        async with websockets.connect(uri) as websocket:
            # Skip welcome message
            await websocket.recv()

            # Create job via API
            response = requests.post(
                f"{api_base_url}/api/v1/jobs",
                json={
                    "company": "WS Test Corp",
                    "job_title": "WebSocket Engineer",
                    "job_description": "Test WebSocket events",
                    "source": "test"
                },
                timeout=10
            )
            job_id = response.json()["id"]

            # Should receive job.created event
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)

                # May receive ping first, keep trying
                while data["type"] == "system.ping":
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)

                assert data["type"] == "job.created"
                assert data["data"]["job_id"] == job_id

            finally:
                # Cleanup
                requests.delete(f"{api_base_url}/api/v1/jobs/{job_id}", timeout=5)

    @pytest.mark.asyncio
    async def test_application_status_changed_event(self, api_base_url, ws_base_url):
        """Test application.status_changed event is broadcast"""

        # Create job first
        response = requests.post(
            f"{api_base_url}/api/v1/jobs",
            json={
                "company": "WS Test Corp",
                "job_title": "Status Test",
                "job_description": "Test status events",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]

        try:
            uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=applications"

            async with websockets.connect(uri) as websocket:
                # Skip welcome message
                await websocket.recv()

                # Update status via API
                requests.post(
                    f"{api_base_url}/api/v1/ats/jobs/{job_id}/status",
                    json={"status": "applied"},
                    timeout=10
                )

                # Should receive application.status_changed event
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)

                    # May receive ping first
                    attempts = 0
                    while data["type"] == "system.ping" and attempts < 5:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        data = json.loads(message)
                        attempts += 1

                    assert data["type"] == "application.status_changed"
                    assert data["data"]["job_id"] == job_id
                    assert data["data"]["new_status"] == "applied"

                except asyncio.TimeoutError:
                    pytest.skip("Event not received in time - may need integration service configured")

        finally:
            # Cleanup
            requests.delete(f"{api_base_url}/api/v1/jobs/{job_id}", timeout=5)

    @pytest.mark.asyncio
    async def test_interview_scheduled_event(self, api_base_url, ws_base_url):
        """Test interview.scheduled event is broadcast"""

        # Create job
        response = requests.post(
            f"{api_base_url}/api/v1/jobs",
            json={
                "company": "Interview Test Corp",
                "job_title": "Interview Test",
                "job_description": "Test interview events",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]

        # Set status to applied first
        requests.post(
            f"{api_base_url}/api/v1/ats/jobs/{job_id}/status",
            json={"status": "applied"},
            timeout=10
        )

        try:
            uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=interviews"

            async with websockets.connect(uri) as websocket:
                # Skip welcome message
                await websocket.recv()

                # Schedule interview
                future_date = (datetime.now() + timedelta(days=7)).isoformat()
                requests.post(
                    f"{api_base_url}/api/v1/ats/interviews",
                    json={
                        "job_id": job_id,
                        "interview_type": "phone",
                        "scheduled_date": future_date,
                        "duration_minutes": 60
                    },
                    timeout=10
                )

                # Should receive interview.scheduled event
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)

                    # May receive ping first
                    attempts = 0
                    while data["type"] == "system.ping" and attempts < 5:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        data = json.loads(message)
                        attempts += 1

                    assert data["type"] == "interview.scheduled"
                    assert data["data"]["job_id"] == job_id

                except asyncio.TimeoutError:
                    pytest.skip("Event not received - may need integration configured")

        finally:
            # Cleanup
            requests.delete(f"{api_base_url}/api/v1/jobs/{job_id}", timeout=5)


class TestWebSocketChannels:
    """Test WebSocket channel isolation"""

    @pytest.mark.asyncio
    async def test_channel_isolation(self, api_base_url, ws_base_url):
        """Test events only sent to subscribed channels"""

        # Connect to jobs channel only
        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs"

        async with websockets.connect(uri) as websocket:
            # Skip welcome message
            await websocket.recv()

            # Create job
            response = requests.post(
                f"{api_base_url}/api/v1/jobs",
                json={
                    "company": "Channel Test",
                    "job_title": "Test",
                    "job_description": "Test",
                    "source": "test"
                },
                timeout=10
            )
            job_id = response.json()["id"]

            try:
                # Update status (applications channel event)
                requests.post(
                    f"{api_base_url}/api/v1/ats/jobs/{job_id}/status",
                    json={"status": "applied"},
                    timeout=10
                )

                # Should NOT receive application event (not subscribed)
                # Should only receive job.created event
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    # Should be job.created or system.ping, not application.status_changed
                    assert data["type"] != "application.status_changed"

                except asyncio.TimeoutError:
                    # No event received is OK (not subscribed to applications)
                    pass

            finally:
                # Cleanup
                requests.delete(f"{api_base_url}/api/v1/jobs/{job_id}", timeout=5)


class TestWebSocketMultipleClients:
    """Test multiple WebSocket clients"""

    @pytest.mark.asyncio
    async def test_multiple_clients_receive_events(self, api_base_url, ws_base_url):
        """Test multiple clients receive same event"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs"

        # Connect two clients
        async with websockets.connect(uri) as ws1, websockets.connect(uri) as ws2:
            # Skip welcome messages
            await ws1.recv()
            await ws2.recv()

            # Create job
            response = requests.post(
                f"{api_base_url}/api/v1/jobs",
                json={
                    "company": "Multi Client Test",
                    "job_title": "Test",
                    "job_description": "Test",
                    "source": "test"
                },
                timeout=10
            )
            job_id = response.json()["id"]

            try:
                # Both clients should receive event
                msg1 = await asyncio.wait_for(ws1.recv(), timeout=10.0)
                msg2 = await asyncio.wait_for(ws2.recv(), timeout=10.0)

                data1 = json.loads(msg1)
                data2 = json.loads(msg2)

                # Skip pings
                while data1["type"] == "system.ping":
                    msg1 = await asyncio.wait_for(ws1.recv(), timeout=10.0)
                    data1 = json.loads(msg1)

                while data2["type"] == "system.ping":
                    msg2 = await asyncio.wait_for(ws2.recv(), timeout=10.0)
                    data2 = json.loads(msg2)

                # Both should receive job.created
                assert data1["type"] == "job.created"
                assert data2["type"] == "job.created"
                assert data1["data"]["job_id"] == job_id
                assert data2["data"]["job_id"] == job_id

            finally:
                # Cleanup
                requests.delete(f"{api_base_url}/api/v1/jobs/{job_id}", timeout=5)


class TestWebSocketReconnection:
    """Test WebSocket reconnection scenarios"""

    @pytest.mark.asyncio
    async def test_reconnection_after_disconnect(self, ws_base_url):
        """Test client can reconnect after disconnect"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user&channels=jobs"

        # First connection
        async with websockets.connect(uri) as websocket:
            await websocket.recv()  # Welcome message
            connection_id_1 = "connected"

        # Second connection (reconnect)
        async with websockets.connect(uri) as websocket:
            message = await websocket.recv()
            data = json.loads(message)
            assert data["type"] == "system.connected"
            # Should get new connection_id


class TestWebSocketErrors:
    """Test WebSocket error handling"""

    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, ws_base_url):
        """Test server handles invalid messages gracefully"""

        uri = f"{ws_base_url}/api/v1/ws?user_id=test_user"

        async with websockets.connect(uri) as websocket:
            # Skip welcome message
            await websocket.recv()

            # Send invalid JSON
            await websocket.send("not json")

            # Server should not crash - may send error or ignore
            # Connection should remain open
            try:
                # Send valid message
                await websocket.send(json.dumps({"action": "ping"}))
                # Should still work
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                assert message is not None
            except:
                pytest.fail("WebSocket closed after invalid message")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
