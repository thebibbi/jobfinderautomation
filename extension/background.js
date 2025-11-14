// Background service worker for the extension

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'JOB_PROCESSED') {
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: 'Job Analysis Complete',
      message: `Match Score: ${message.data.matchScore}% - ${message.data.jobTitle || 'Job'}`,
      priority: 2
    });

    // Open results in new tab (optional)
    if (message.data.driveUrl) {
      chrome.tabs.create({
        url: message.data.driveUrl,
        active: false
      });
    }
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Send message to content script to trigger analysis
  chrome.tabs.sendMessage(tab.id, { action: 'TRIGGER_ANALYSIS' });
});
