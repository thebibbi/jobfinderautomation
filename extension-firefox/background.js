// Enhanced background service worker with WebSocket support

// WebSocket connection
let ws = null;
let wsReconnectTimeout = null;
let connectionAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

// Connection state
let isConnected = false;
let pendingNotifications = [];

// Initialize WebSocket connection
async function initWebSocket() {
  const settings = await browser.storage.sync.get(['apiUrl']);
  const apiUrl = settings.apiUrl || 'http://localhost:8000';

  // Handle WebSocket URL based on environment
  let wsUrl;
  if (apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1')) {
    // Local development: use ws:// without SSL
    wsUrl = apiUrl.replace(/^https?/, 'ws') + '/api/v1/ws?user_id=extension&channels=jobs,applications,interviews,recommendations,skills,followups';
  } else {
    // Production: use wss:// with SSL
    wsUrl = apiUrl.replace(/^https?/, 'wss') + '/api/v1/ws?user_id=extension&channels=jobs,applications,interviews,recommendations,skills,followups';
  }

  console.log('🔌 Connecting to WebSocket:', wsUrl);

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      isConnected = true;
      connectionAttempts = 0;

      // Update badge to show connected status
      browser.action.setBadgeText({ text: '' });
      browser.action.setBadgeBackgroundColor({ color: '#10b981' });

      // Send pending notifications if any
      if (pendingNotifications.length > 0) {
        pendingNotifications = [];
      }

      if (wsReconnectTimeout) {
        clearTimeout(wsReconnectTimeout);
        wsReconnectTimeout = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      isConnected = false;
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket closed');
      isConnected = false;

      // Update badge to show disconnected
      browser.action.setBadgeText({ text: '!' });
      browser.action.setBadgeBackgroundColor({ color: '#ef4444' });

      // Attempt reconnection
      if (connectionAttempts < MAX_RECONNECT_ATTEMPTS) {
        connectionAttempts++;
        const delay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${connectionAttempts}/${MAX_RECONNECT_ATTEMPTS})`);

        wsReconnectTimeout = setTimeout(() => {
          initWebSocket();
        }, delay);
      }
    };

  } catch (error) {
    console.error('Failed to create WebSocket:', error);
  }
}

// Handle WebSocket messages
function handleWebSocketMessage(message) {
  console.log('📨 WebSocket event:', message.type);

  switch (message.type) {
    case 'system.connected':
      console.log('Connected to WebSocket server');
      break;

    case 'system.ping':
      // Respond to keep-alive ping
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'pong' }));
      }
      break;

    case 'job.created':
      showNotification(
        'New Job Saved',
        `${message.data.job_title} at ${message.data.company}`,
        'info'
      );
      break;

    case 'job.analyzing':
      showNotification(
        'Analyzing Job',
        `Analyzing ${message.data.job_title} at ${message.data.company}...`,
        'info'
      );
      break;

    case 'job.analyzed':
      const score = message.data.match_score;
      const recommendation = message.data.recommendation;

      let emoji = '📊';
      if (score >= 90) emoji = '🎯';
      else if (score >= 80) emoji = '✨';
      else if (score >= 70) emoji = '👍';

      showNotification(
        `${emoji} Job Analysis Complete`,
        `Match Score: ${score}% - ${getRecommendationText(recommendation)}`,
        score >= 80 ? 'success' : 'info'
      );

      // Update badge with score
      browser.action.setBadgeText({ text: `${Math.round(score)}` });
      browser.action.setBadgeBackgroundColor({
        color: score >= 80 ? '#10b981' : score >= 70 ? '#f59e0b' : '#6b7280'
      });
      break;

    case 'application.status_changed':
      const { old_status, new_status, company, job_title } = message.data;

      showNotification(
        'Application Status Updated',
        `${job_title} at ${company}: ${old_status} → ${new_status}`,
        'info'
      );
      break;

    case 'interview.scheduled':
      showNotification(
        '📅 Interview Scheduled',
        `${message.data.interview_type} interview for ${message.data.job_title} at ${message.data.company}`,
        'success',
        { requireInteraction: true }
      );
      break;

    case 'interview.reminder':
      showNotification(
        '⏰ Interview Reminder',
        `Interview in ${message.data.time_until}! ${message.data.interview_type} with ${message.data.company}`,
        'warning',
        { requireInteraction: true }
      );
      break;

    case 'skill_gap.completed':
      showNotification(
        'Skills Analysis Complete',
        `Overall match: ${message.data.overall_match}% (${message.data.missing_skills} skills to learn)`,
        'info'
      );
      break;

    case 'followup.due':
      showNotification(
        '📧 Follow-up Due',
        `Follow up with ${message.data.company} in ${message.data.hours_until_due} hours`,
        'warning'
      );
      break;

    case 'recommendations.new':
      showNotification(
        '✨ New Recommendations',
        `${message.data.count} new job recommendations available`,
        'info'
      );

      // Update badge
      browser.action.setBadgeText({ text: `${message.data.count}` });
      browser.action.setBadgeBackgroundColor({ color: '#8b5cf6' });
      break;

    default:
      console.log('Unhandled message type:', message.type);
  }

  // Broadcast to popup if open
  broadcastToPopup(message);
}

// Show Chrome notification
function showNotification(title, message, type = 'info', options = {}) {
  const iconUrl = getIconForType(type);

  browser.notifications.create({
    type: 'basic',
    iconUrl,
    title,
    message,
    priority: type === 'warning' ? 2 : 1,
    ...options
  });
}

// Get icon based on notification type
function getIconForType(type) {
  // In production, use different icons for different types
  return 'icons/icon128.png';
}

// Get recommendation text
function getRecommendationText(recommendation) {
  const texts = {
    'apply_now': 'Apply Now! 🎯',
    'apply_with_confidence': 'Apply with Confidence ✨',
    'consider_carefully': 'Consider Carefully 🤔',
    'not_recommended': 'Not Recommended ⚠️'
  };
  return texts[recommendation] || recommendation;
}

// Broadcast message to popup
function broadcastToPopup(message) {
  browser.runtime.sendMessage({
    type: 'WEBSOCKET_EVENT',
    data: message
  }).catch(() => {
    // Popup not open, ignore
  });
}

// Listen for messages from content script and popup
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'JOB_PROCESSED') {
    // Legacy: Show notification for manually processed job
    const { matchScore, jobTitle, driveUrl } = message.data;

    showNotification(
      'Job Processing Complete',
      `${jobTitle}: ${matchScore}% match`,
      matchScore >= 80 ? 'success' : 'info'
    );

    // Open Drive folder if available
    if (driveUrl) {
      browser.tabs.create({
        url: driveUrl,
        active: false
      });
    }
  }

  if (message.type === 'GET_CONNECTION_STATUS') {
    sendResponse({ connected: isConnected });
  }

  if (message.type === 'RECONNECT_WEBSOCKET') {
    if (ws) {
      ws.close();
    }
    initWebSocket();
    sendResponse({ success: true });
  }
});

// Handle extension icon click
browser.action.onClicked.addListener((tab) => {
  // Open popup (default behavior)
  // If popup doesn't exist, send message to content script
  browser.tabs.sendMessage(tab.id, { action: 'TRIGGER_ANALYSIS' }).catch(() => {
    // Content script not loaded
    console.log('Content script not available on this page');
  });
});

// Handle notification clicks
browser.notifications.onClicked.addListener((notificationId) => {
  // Open popup or dashboard
  browser.storage.sync.get(['apiUrl'], (settings) => {
    const apiUrl = settings.apiUrl || 'http://localhost:8000';
    browser.tabs.create({ url: `${apiUrl}/dashboard` });
  });
});

// Initialize on startup
browser.runtime.onStartup.addListener(() => {
  console.log('Extension started');
  initWebSocket();
});

// Initialize on install
browser.runtime.onInstalled.addListener(() => {
  console.log('Extension installed/updated');

  // Set default settings
  browser.storage.sync.get(['apiUrl'], (settings) => {
    if (!settings.apiUrl) {
      browser.storage.sync.set({
        apiUrl: 'http://localhost:8000',
        minScore: 70,
        autoGenerate: true,
        notifications: true
      });
    }
  });

  initWebSocket();
});

// Initialize WebSocket on script load
initWebSocket();

// Periodic WebSocket health check (every 60 seconds)
setInterval(() => {
  if (!isConnected && connectionAttempts < MAX_RECONNECT_ATTEMPTS) {
    console.log('WebSocket health check: not connected, attempting reconnect');
    initWebSocket();
  }
}, 60000);
