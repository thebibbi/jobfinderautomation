// Popup JavaScript

document.addEventListener('DOMContentLoaded', async () => {
  // Load saved settings
  const settings = await chrome.storage.sync.get(['apiUrl', 'minScore', 'autoGenerate']);

  document.getElementById('apiUrl').value = settings.apiUrl || 'http://localhost:8000';
  document.getElementById('minScore').value = settings.minScore || 70;
  document.getElementById('autoGenerate').checked = settings.autoGenerate !== false;

  // Save settings button
  document.getElementById('saveSettings').addEventListener('click', async () => {
    const apiUrl = document.getElementById('apiUrl').value;
    const minScore = parseInt(document.getElementById('minScore').value);
    const autoGenerate = document.getElementById('autoGenerate').checked;

    await chrome.storage.sync.set({
      apiUrl,
      minScore,
      autoGenerate
    });

    showStatus('Settings saved successfully!', 'success');
  });

  // View dashboard link
  document.getElementById('viewDashboard').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.storage.sync.get(['apiUrl'], (settings) => {
      const apiUrl = settings.apiUrl || 'http://localhost:8000';
      chrome.tabs.create({ url: `${apiUrl}/dashboard` });
    });
  });
});

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;

  setTimeout(() => {
    status.classList.add('hidden');
  }, 3000);
}
