# WebSocket Real-time Updates Guide

Complete guide to using real-time WebSocket updates in the Job Automation System.

---

## Table of Contents

1. [Overview](#overview)
2. [Connection Setup](#connection-setup)
3. [Channel Subscription](#channel-subscription)
4. [Event Types](#event-types)
5. [Client Implementation Examples](#client-implementation-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The WebSocket API provides real-time, bi-directional communication between the server and clients. Receive instant notifications for:

- Job analysis completion
- Application status changes
- New recommendations
- Interview scheduling
- Skills gap analysis results
- Follow-up reminders
- System notifications

**Benefits**:
- **Instant Updates**: No polling required
- **Lower Latency**: Sub-second notification delivery
- **Reduced Load**: Single persistent connection vs multiple HTTP requests
- **Bi-directional**: Client can also send messages to server

**Architecture**:
```
Client (Browser/Extension) <--WebSocket--> FastAPI Server <--> Redis Pub/Sub
                                                |
                                                ├─> Job Analysis Service
                                                ├─> ATS Service
                                                ├─> Calendar Service
                                                └─> Recommendation Engine
```

---

## Connection Setup

### Endpoint

**WebSocket URL**: `ws://localhost:8000/api/v1/ws`
**Production URL**: `wss://api.yourdomain.com/api/v1/ws`

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | No | User identifier for multi-device sync |
| `channels` | string | No | Comma-separated list of channels to subscribe |

### Basic Connection

**JavaScript (Browser)**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?user_id=user123&channels=jobs,applications');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  handleEvent(message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('WebSocket closed:', event.code, event.reason);
  // Implement reconnection logic
};
```

**Python Client**:
```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/api/v1/ws?user_id=user123&channels=jobs,applications"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            await handle_event(data)

asyncio.run(connect())
```

### Welcome Message

Upon successful connection, you'll receive:

```json
{
  "type": "system.connected",
  "data": {
    "connection_id": "conn_abc123",
    "user_id": "user123",
    "channels": ["jobs", "applications"],
    "message": "Connected to WebSocket server",
    "timestamp": "2025-11-14T15:00:00Z"
  },
  "timestamp": "2025-11-14T15:00:00Z"
}
```

**Connection ID**: Unique identifier for this connection
**User ID**: Your user identifier (for multi-device sync)
**Channels**: Subscribed channels

---

## Channel Subscription

### Available Channels

| Channel | Description | Events |
|---------|-------------|--------|
| `jobs` | Job-related events | `job.created`, `job.analyzing`, `job.analyzed` |
| `applications` | Application tracking | `application.status_changed`, `application.updated` |
| `recommendations` | New recommendations | `recommendations.new`, `recommendations.updated` |
| `skills` | Skills gap analysis | `skill_gap.completed`, `skill_gap.updated` |
| `followups` | Follow-up reminders | `followup.due`, `followup.sent` |
| `interviews` | Interview events | `interview.scheduled`, `interview.updated`, `interview.reminder` |
| `system` | System notifications | `system.notification`, `system.maintenance`, `system.ping` |

### Subscribe on Connection

Include channels in query parameter:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?channels=jobs,applications,interviews');
```

### Subscribe After Connection

Send subscription message:

```javascript
// Subscribe to channel
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'recommendations'
}));

// Server response
{
  "type": "system.subscribed",
  "data": {
    "channel": "recommendations",
    "subscriber_count": 8
  },
  "timestamp": "2025-11-14T15:01:00Z"
}
```

### Unsubscribe from Channel

```javascript
// Unsubscribe from channel
ws.send(JSON.stringify({
  action: 'unsubscribe',
  channel: 'recommendations'
}));

// Server response
{
  "type": "system.unsubscribed",
  "data": {
    "channel": "recommendations"
  },
  "timestamp": "2025-11-14T15:02:00Z"
}
```

### List Subscribed Channels

```javascript
ws.send(JSON.stringify({
  action: 'list_channels'
}));

// Server response
{
  "type": "system.channels",
  "data": {
    "channels": ["jobs", "applications", "interviews"]
  },
  "timestamp": "2025-11-14T15:03:00Z"
}
```

---

## Event Types

All events follow this format:

```json
{
  "type": "event.type",
  "data": {
    // Event-specific data
  },
  "timestamp": "2025-11-14T15:00:00Z"
}
```

### Job Events

#### job.created

Sent when new job is added to database.

```json
{
  "type": "job.created",
  "data": {
    "job_id": 42,
    "company": "Google",
    "job_title": "Senior Software Engineer",
    "location": "Mountain View, CA",
    "source": "linkedin"
  },
  "timestamp": "2025-11-14T15:00:00Z"
}
```

#### job.analyzing

Sent when job analysis starts.

```json
{
  "type": "job.analyzing",
  "data": {
    "job_id": 42,
    "company": "Google",
    "job_title": "Senior Software Engineer"
  },
  "timestamp": "2025-11-14T15:01:00Z"
}
```

#### job.analyzed

Sent when job analysis completes.

```json
{
  "type": "job.analyzed",
  "data": {
    "job_id": 42,
    "match_score": 85.5,
    "recommendation": "apply_now",
    "strengths": [
      "Strong Python match",
      "Location preference aligns"
    ],
    "concerns": [
      "Requires 7+ years experience"
    ]
  },
  "timestamp": "2025-11-14T15:02:00Z"
}
```

**UI Integration**:
```javascript
function handleJobAnalyzed(data) {
  // Update job card with match score
  updateJobCard(data.job_id, {
    matchScore: data.match_score,
    recommendation: data.recommendation,
    badge: data.match_score >= 80 ? 'Excellent Match' : 'Good Match'
  });

  // Show notification
  showNotification(`Job analyzed: ${data.match_score}% match`);

  // Update dashboard stats
  refreshDashboardStats();
}
```

---

### Application Events

#### application.status_changed

Sent when application status changes.

```json
{
  "type": "application.status_changed",
  "data": {
    "job_id": 42,
    "company": "Google",
    "job_title": "Senior Software Engineer",
    "old_status": "applied",
    "new_status": "interviewing",
    "timestamp": "2025-11-14T15:05:00Z"
  },
  "timestamp": "2025-11-14T15:05:00Z"
}
```

**UI Integration**:
```javascript
function handleStatusChanged(data) {
  // Update application status badge
  updateApplicationStatus(data.job_id, data.new_status);

  // Move card to new column (Kanban board)
  moveCardToColumn(data.job_id, data.new_status);

  // Show toast notification
  showToast(`Application moved to ${data.new_status}`);

  // Play sound for important status changes
  if (data.new_status === 'offer_received') {
    playSound('celebration');
  }
}
```

---

### Recommendation Events

#### recommendations.new

Sent when new recommendations are generated.

```json
{
  "type": "recommendations.new",
  "data": {
    "count": 10,
    "top_recommendations": [
      {
        "job_id": 50,
        "company": "Netflix",
        "job_title": "Backend Engineer",
        "score": 92.5
      },
      {
        "job_id": 51,
        "company": "Uber",
        "job_title": "Staff Engineer",
        "score": 88.3
      }
    ],
    "generated_at": "2025-11-14T15:10:00Z"
  },
  "timestamp": "2025-11-14T15:10:00Z"
}
```

**UI Integration**:
```javascript
function handleNewRecommendations(data) {
  // Show badge on recommendations tab
  updateRecommendationsBadge(data.count);

  // Show notification
  showNotification(`${data.count} new job recommendations`);

  // Refresh recommendations list (if visible)
  if (isRecommendationsTabActive()) {
    refreshRecommendations();
  }
}
```

---

### Interview Events

#### interview.scheduled

Sent when interview is scheduled.

```json
{
  "type": "interview.scheduled",
  "data": {
    "interview_id": 5,
    "job_id": 42,
    "company": "Google",
    "job_title": "Senior Software Engineer",
    "interview_type": "technical",
    "scheduled_date": "2025-11-15T14:00:00Z",
    "duration_minutes": 90,
    "calendar_event_id": "cal_abc123"
  },
  "timestamp": "2025-11-14T15:15:00Z"
}
```

**UI Integration**:
```javascript
function handleInterviewScheduled(data) {
  // Add to calendar widget
  addToCalendarWidget(data);

  // Show notification with countdown
  const daysUntil = getDaysUntil(data.scheduled_date);
  showNotification(`Interview scheduled in ${daysUntil} days`);

  // Update application timeline
  addToTimeline(data.job_id, 'interview_scheduled', data);
}
```

#### interview.reminder

Sent before interview (1 day, 1 hour, 15 min).

```json
{
  "type": "interview.reminder",
  "data": {
    "interview_id": 5,
    "job_id": 42,
    "company": "Google",
    "interview_type": "technical",
    "scheduled_date": "2025-11-15T14:00:00Z",
    "time_until": "15 minutes"
  },
  "timestamp": "2025-11-15T13:45:00Z"
}
```

**UI Integration**:
```javascript
function handleInterviewReminder(data) {
  // Show prominent notification
  showUrgentNotification(
    `Interview in ${data.time_until}!`,
    `${data.interview_type} interview with ${data.company}`
  );

  // Open preparation notes (if < 1 hour)
  if (data.time_until.includes('minutes')) {
    openPreparationNotes(data.interview_id);
  }
}
```

---

### Skills Events

#### skill_gap.completed

Sent when skills gap analysis completes.

```json
{
  "type": "skill_gap.completed",
  "data": {
    "job_id": 42,
    "overall_match": 78.5,
    "matching_skills": 8,
    "missing_skills": 3,
    "missing_skills_list": [
      {
        "skill": "Kubernetes",
        "importance": "high"
      },
      {
        "skill": "GraphQL",
        "importance": "medium"
      }
    ]
  },
  "timestamp": "2025-11-14T15:20:00Z"
}
```

**UI Integration**:
```javascript
function handleSkillGapCompleted(data) {
  // Update job card with skills badge
  updateJobCard(data.job_id, {
    skillsMatch: data.overall_match,
    missingSkills: data.missing_skills
  });

  // Show learning recommendations
  if (data.missing_skills > 0) {
    showLearningRecommendations(data.job_id, data.missing_skills_list);
  }
}
```

---

### Follow-up Events

#### followup.due

Sent when follow-up is due soon.

```json
{
  "type": "followup.due",
  "data": {
    "followup_id": 10,
    "job_id": 42,
    "company": "Google",
    "job_title": "Senior Software Engineer",
    "followup_type": "post_application",
    "scheduled_date": "2025-11-14T17:00:00Z",
    "hours_until_due": 2
  },
  "timestamp": "2025-11-14T15:25:00Z"
}
```

**UI Integration**:
```javascript
function handleFollowUpDue(data) {
  // Show notification
  showNotification(
    `Follow-up due in ${data.hours_until_due} hours`,
    `${data.company} - ${data.followup_type}`
  );

  // Add to action items list
  addToActionItems({
    type: 'follow_up',
    job_id: data.job_id,
    due: data.scheduled_date
  });
}
```

---

### System Events

#### system.ping

Keep-alive ping (every 30 seconds).

```json
{
  "type": "system.ping",
  "data": {
    "timestamp": "2025-11-14T15:30:00Z"
  },
  "timestamp": "2025-11-14T15:30:00Z"
}
```

**Client Response**:
```javascript
// Respond to ping to confirm connection alive
ws.send(JSON.stringify({
  action: 'pong'
}));
```

#### system.notification

General system notification.

```json
{
  "type": "system.notification",
  "data": {
    "message": "System maintenance in 5 minutes",
    "severity": "warning",
    "action_required": false
  },
  "timestamp": "2025-11-14T15:35:00Z"
}
```

---

## Client Implementation Examples

### React Component

```javascript
import { useEffect, useState, useCallback } from 'react';

function useWebSocket(userId, channels) {
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const channelStr = channels.join(',');
    const socket = new WebSocket(
      `ws://localhost:8000/api/v1/ws?user_id=${userId}&channels=${channelStr}`
    );

    socket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
      handleEvent(message);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    socket.onclose = () => {
      console.log('WebSocket closed');
      setConnected(false);
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (socket.readyState === WebSocket.CLOSED) {
          window.location.reload();
        }
      }, 3000);
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, [userId, channels]);

  const handleEvent = useCallback((message) => {
    switch (message.type) {
      case 'job.analyzed':
        console.log('Job analyzed:', message.data);
        break;
      case 'application.status_changed':
        console.log('Status changed:', message.data);
        break;
      case 'interview.scheduled':
        console.log('Interview scheduled:', message.data);
        break;
      default:
        console.log('Unknown event:', message.type);
    }
  }, []);

  const subscribe = useCallback((channel) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'subscribe', channel }));
    }
  }, [ws]);

  const unsubscribe = useCallback((channel) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'unsubscribe', channel }));
    }
  }, [ws]);

  return { connected, messages, subscribe, unsubscribe };
}

// Usage in component
function JobDashboard() {
  const { connected, messages } = useWebSocket('user123', ['jobs', 'applications']);

  return (
    <div>
      <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
      {messages.map((msg, i) => (
        <div key={i}>{msg.type}: {JSON.stringify(msg.data)}</div>
      ))}
    </div>
  );
}
```

### Chrome Extension Background Script

```javascript
// background.js
let ws = null;
let reconnectTimeout = null;

function connectWebSocket() {
  ws = new WebSocket('ws://localhost:8000/api/v1/ws?user_id=extension&channels=jobs,applications');

  ws.onopen = () => {
    console.log('Extension WebSocket connected');
    chrome.action.setBadgeText({ text: '' });
    chrome.action.setBadgeBackgroundColor({ color: '#00FF00' });

    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleWebSocketMessage(message);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket closed, reconnecting...');
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#FF0000' });

    // Reconnect after 5 seconds
    reconnectTimeout = setTimeout(connectWebSocket, 5000);
  };
}

function handleWebSocketMessage(message) {
  switch (message.type) {
    case 'job.analyzed':
      // Show notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon.png',
        title: 'Job Analyzed',
        message: `Match score: ${message.data.match_score}%`
      });

      // Update badge
      chrome.action.setBadgeText({ text: 'NEW' });
      break;

    case 'interview.scheduled':
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon.png',
        title: 'Interview Scheduled',
        message: `${message.data.company} - ${message.data.interview_type}`
      });
      break;

    case 'followup.due':
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon.png',
        title: 'Follow-up Due',
        message: `Follow up with ${message.data.company}`
      });
      break;
  }

  // Broadcast to popup/content scripts
  chrome.runtime.sendMessage({
    type: 'websocket_event',
    data: message
  });
}

// Start connection
connectWebSocket();
```

---

## Best Practices

### 1. Implement Reconnection Logic

WebSocket connections can drop. Always implement reconnection:

```javascript
class WebSocketManager {
  constructor(url, options = {}) {
    this.url = url;
    this.reconnectDelay = options.reconnectDelay || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    this.reconnectAttempts = 0;
    this.ws = null;
    this.eventHandlers = {};
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectAttempts = 0;
      this.onConnected();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('Disconnected');
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('Error:', error);
    };
  }

  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  on(eventType, handler) {
    this.eventHandlers[eventType] = handler;
  }

  handleMessage(message) {
    const handler = this.eventHandlers[message.type];
    if (handler) {
      handler(message.data);
    }
  }

  onConnected() {
    // Override in subclass
  }
}

// Usage
const wsManager = new WebSocketManager('ws://localhost:8000/api/v1/ws?user_id=user123&channels=jobs');
wsManager.on('job.analyzed', (data) => {
  console.log('Job analyzed:', data);
});
wsManager.connect();
```

### 2. Handle Connection Status in UI

Show connection status to user:

```javascript
function ConnectionStatus({ connected }) {
  return (
    <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
      {connected ? (
        <>
          <span className="indicator green"></span>
          Real-time updates active
        </>
      ) : (
        <>
          <span className="indicator red"></span>
          Reconnecting...
        </>
      )}
    </div>
  );
}
```

### 3. Deduplicate Events

Server may send duplicate events. Implement deduplication:

```javascript
class EventDeduplicator {
  constructor(ttlMs = 5000) {
    this.seen = new Map();
    this.ttl = ttlMs;
  }

  isDuplicate(eventType, eventId) {
    const key = `${eventType}:${eventId}`;

    if (this.seen.has(key)) {
      return true;
    }

    this.seen.set(key, Date.now());

    // Cleanup old entries
    for (const [k, timestamp] of this.seen.entries()) {
      if (Date.now() - timestamp > this.ttl) {
        this.seen.delete(k);
      }
    }

    return false;
  }
}

const deduplicator = new EventDeduplicator();

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  const eventId = message.data.job_id || message.data.id;

  if (!deduplicator.isDuplicate(message.type, eventId)) {
    handleEvent(message);
  }
};
```

### 4. Queue Events During Reconnection

Buffer events received while reconnecting:

```javascript
class EventQueue {
  constructor() {
    this.queue = [];
    this.processing = false;
  }

  add(event) {
    this.queue.push(event);
    if (!this.processing) {
      this.processQueue();
    }
  }

  async processQueue() {
    this.processing = true;

    while (this.queue.length > 0) {
      const event = this.queue.shift();
      await handleEvent(event);
    }

    this.processing = false;
  }
}
```

### 5. Implement Heartbeat Monitoring

Monitor heartbeat and reconnect if stale:

```javascript
let lastPingTime = Date.now();
let heartbeatInterval = null;

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'system.ping') {
    lastPingTime = Date.now();
    ws.send(JSON.stringify({ action: 'pong' }));
  } else {
    handleEvent(message);
  }
};

// Check heartbeat every 45 seconds
heartbeatInterval = setInterval(() => {
  const timeSinceLastPing = Date.now() - lastPingTime;

  if (timeSinceLastPing > 45000) {
    console.warn('No ping received, reconnecting...');
    ws.close();
  }
}, 45000);
```

---

## Troubleshooting

### Connection Fails Immediately

**Problem**: WebSocket closes immediately after connecting

**Solutions**:
1. Check if backend is running: `curl http://localhost:8000/health`
2. Verify WebSocket endpoint: `ws://` (not `http://`)
3. Check browser console for CORS errors
4. Ensure query parameters are properly encoded

### Events Not Received

**Problem**: Connected but not receiving events

**Solutions**:
1. Verify channel subscription:
   ```javascript
   ws.send(JSON.stringify({ action: 'list_channels' }));
   ```
2. Check if events are being generated (test with API calls)
3. Verify user_id matches (for user-specific events)
4. Check browser console for JSON parsing errors

### Frequent Disconnections

**Problem**: WebSocket disconnects frequently

**Solutions**:
1. Implement ping/pong heartbeat
2. Check network stability
3. Increase server timeout settings
4. Use WSS (secure WebSocket) in production

### High Memory Usage

**Problem**: Client memory grows over time

**Solutions**:
1. Implement message buffer limits:
   ```javascript
   const MAX_MESSAGES = 100;
   setMessages(prev => [...prev, message].slice(-MAX_MESSAGES));
   ```
2. Clean up event listeners on unmount
3. Implement event deduplication

### CORS Errors

**Problem**: CORS policy blocks WebSocket connection

**Solution**: Backend configuration already allows all origins in development. For production, add your domain to `allow_origins` in `backend/app/main.py`.

---

## Testing WebSocket Connection

### Using wscat (CLI)

```bash
npm install -g wscat
wscat -c "ws://localhost:8000/api/v1/ws?user_id=test&channels=jobs"

# Connected
< {"type":"system.connected","data":{"connection_id":"conn_123"},"timestamp":"..."}

# Subscribe to channel
> {"action":"subscribe","channel":"applications"}

# Wait for events...
< {"type":"job.analyzed","data":{"job_id":42,"match_score":85.5},"timestamp":"..."}
```

### Using Browser Console

```javascript
// Open browser console on http://localhost:3000 (your frontend)
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?user_id=test&channels=jobs,applications');

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Closed');

// Trigger test event by creating a job via API
fetch('http://localhost:8000/api/v1/jobs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    company: 'Test Corp',
    job_title: 'Test Engineer',
    job_description: 'Test job',
    job_url: 'https://test.com/job/123',
    location: 'Test City',
    source: 'test'
  })
});

// Watch console for job.created and job.analyzed events
```

---

## Performance Considerations

- **Connection Pooling**: Server supports multiple connections per user
- **Message Size**: Keep event payloads under 64KB
- **Event Frequency**: Server throttles high-frequency events
- **Client Buffering**: Implement client-side buffering for rapid events
- **Bandwidth**: WebSocket uses ~1KB per event, minimal overhead

---

## Security

- **Authentication**: Implement token-based auth in production
- **TLS**: Use WSS (WebSocket Secure) in production
- **Rate Limiting**: Server limits messages per connection
- **Input Validation**: Server validates all client messages
- **XSS Protection**: Always sanitize event data before rendering in UI

---

## Next Steps

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Integration Guide](./INTEGRATION_GUIDE.md) - Cross-feature workflows
- [Authentication Setup](./AUTHENTICATION.md) - OAuth and API keys
