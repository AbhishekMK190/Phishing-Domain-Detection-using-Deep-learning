// PhishGuard Pro - Options Page Script
(() => {
  'use strict';
  
  // DOM elements
  const elements = {
    apiBase: document.getElementById('apiBase'),
    autoCheck: document.getElementById('autoCheck'),
    showSafeNotifications: document.getElementById('showSafeNotifications'),
    enableSounds: document.getElementById('enableSounds'),
    cacheSize: document.getElementById('cacheSize'),
    apiStatus: document.getElementById('apiStatus'),
    testBtn: document.getElementById('testBtn'),
    clearCacheBtn: document.getElementById('clearCacheBtn'),
    saveBtn: document.getElementById('saveBtn'),
    status: document.getElementById('status')
  };
  
  // Initialize options page
  init();
  
  async function init() {
    console.log('🛡️ PhishGuard Pro options initializing...');
    
    // Load current settings
    await loadSettings();
    
    // Set up event listeners
    setupEventListeners();
    
    // Update stats
    await updateStats();
  }
  
  // Set up event listeners
  function setupEventListeners() {
    elements.saveBtn.addEventListener('click', saveSettings);
    elements.testBtn.addEventListener('click', testConnection);
    elements.clearCacheBtn.addEventListener('click', clearCache);
  }
  
  // Load current settings
  async function loadSettings() {
    try {
      const response = await sendMessage({ type: 'GET_SETTINGS' });
      if (response.success) {
        const settings = response.settings;
        
        elements.apiBase.value = settings.apiBase || 'http://127.0.0.1:5000';
        elements.autoCheck.checked = settings.autoCheck !== false;
        elements.showSafeNotifications.checked = settings.showSafeNotifications !== false;
        elements.enableSounds.checked = settings.enableSounds !== false;
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      showStatus('Failed to load settings', 'error');
    }
  }
  
  // Save settings
  async function saveSettings() {
    const settings = {
      apiBase: elements.apiBase.value.trim(),
      autoCheck: elements.autoCheck.checked,
      showSafeNotifications: elements.showSafeNotifications.checked,
      enableSounds: elements.enableSounds.checked
    };
    
    // Validate API base URL
    if (!settings.apiBase) {
      showStatus('Please enter an API base URL', 'error');
      elements.apiBase.focus();
      return;
    }
    
    try {
      new URL(settings.apiBase);
    } catch {
      showStatus('Please enter a valid URL', 'error');
      elements.apiBase.focus();
      return;
    }
    
    try {
      const response = await sendMessage({
        type: 'UPDATE_SETTINGS',
        settings: settings
      });
      
      if (response.success) {
        showStatus('Settings saved successfully!', 'success');
        
        // Update stats after saving
        setTimeout(updateStats, 1000);
      } else {
        showStatus('Failed to save settings', 'error');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      showStatus('Failed to save settings', 'error');
    }
  }
  
  // Test API connection
  async function testConnection() {
    const apiBase = elements.apiBase.value.trim();
    
    if (!apiBase) {
      showStatus('Please enter an API base URL first', 'error');
      elements.apiBase.focus();
      return;
    }
    
    elements.testBtn.textContent = 'Testing...';
    elements.testBtn.disabled = true;
    
    try {
      // Test with a simple domain
      const response = await fetch(`${apiBase}/api/check`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'User-Agent': 'PhishGuard-Pro-Options/2.0'
        },
        body: JSON.stringify({ domain: 'example.com' }),
        signal: AbortSignal.timeout(10000)
      });
      
      if (response.ok) {
        const data = await response.json();
        showStatus('✅ Connection successful! API is responding correctly.', 'success');
        
        // Update API status
        elements.apiStatus.textContent = 'Online';
        elements.apiStatus.style.color = '#059669';
      } else {
        showStatus(`❌ Connection failed: HTTP ${response.status}`, 'error');
        elements.apiStatus.textContent = 'Offline';
        elements.apiStatus.style.color = '#dc2626';
      }
    } catch (error) {
      let errorMessage = '❌ Connection failed: ';
      
      if (error.name === 'TimeoutError') {
        errorMessage += 'Request timed out';
      } else if (error.message.includes('fetch')) {
        errorMessage += 'Unable to reach API server';
      } else {
        errorMessage += error.message;
      }
      
      showStatus(errorMessage, 'error');
      elements.apiStatus.textContent = 'Offline';
      elements.apiStatus.style.color = '#dc2626';
    } finally {
      elements.testBtn.textContent = 'Test Connection';
      elements.testBtn.disabled = false;
    }
  }
  
  // Clear cache
  async function clearCache() {
    if (!confirm('Are you sure you want to clear the cache? This will remove all cached security checks.')) {
      return;
    }
    
    elements.clearCacheBtn.textContent = 'Clearing...';
    elements.clearCacheBtn.disabled = true;
    
    try {
      const response = await sendMessage({ type: 'CLEAR_CACHE' });
      
      if (response.success) {
        showStatus('✅ Cache cleared successfully!', 'success');
        elements.cacheSize.textContent = '0';
      } else {
        showStatus('❌ Failed to clear cache', 'error');
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
      showStatus('❌ Failed to clear cache', 'error');
    } finally {
      elements.clearCacheBtn.textContent = 'Clear Cache';
      elements.clearCacheBtn.disabled = false;
    }
  }
  
  // Update statistics
  async function updateStats() {
    try {
      const response = await sendMessage({ type: 'GET_CACHE_STATS' });
      
      if (response.success && response.stats) {
        const stats = response.stats;
        
        elements.cacheSize.textContent = stats.size.toString();
        
        if (stats.isApiHealthy) {
          elements.apiStatus.textContent = 'Online';
          elements.apiStatus.style.color = '#059669';
        } else {
          elements.apiStatus.textContent = 'Offline';
          elements.apiStatus.style.color = '#dc2626';
        }
      }
    } catch (error) {
      console.error('Failed to update stats:', error);
    }
  }
  
  // Send message to background script
  function sendMessage(message) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(message, (response) => {
          if (chrome.runtime.lastError) {
            resolve({ success: false, error: chrome.runtime.lastError.message });
          } else {
            resolve(response || { success: false, error: 'No response' });
          }
        });
      } catch (error) {
        resolve({ success: false, error: error.message });
      }
    });
  }
  
  // Show status message
  function showStatus(message, type = 'info') {
    elements.status.textContent = message;
    elements.status.className = `status ${type}`;
    elements.status.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      elements.status.style.display = 'none';
    }, 5000);
  }
  
  console.log('🛡️ PhishGuard Pro options ready');
})();
