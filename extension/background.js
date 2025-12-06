// PhishGuard Pro - Enhanced Background Service Worker

// Configuration and initialization
const CONFIG = {
  DEFAULT_API_BASE: 'http://127.0.0.1:5000',
  CHECK_TIMEOUT: 15000,
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
  NOTIFICATION_DURATION: 8000,
  SAFE_NOTIFICATION_DURATION: 4000
};

// In-memory cache for recent checks
const urlCache = new Map();
let isApiHealthy = true;
let lastHealthCheck = 0;

// Initialize extension
chrome.runtime.onInstalled.addListener(async () => {
  // Set default settings
  const settings = await chrome.storage.sync.get({
    apiBase: CONFIG.DEFAULT_API_BASE,
    autoCheck: true,
    showSafeNotifications: true,
    notificationDuration: CONFIG.NOTIFICATION_DURATION,
    enableSounds: true
  });
  
  if (!settings.apiBase) {
    await chrome.storage.sync.set({ apiBase: CONFIG.DEFAULT_API_BASE });
  }
  
  // Set up periodic health checks
  chrome.alarms.create('healthCheck', { periodInMinutes: 5 });
  
  console.log('🛡️ PhishGuard Pro initialized');
});

// Handle alarms
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'healthCheck') {
    await checkApiHealth();
  }
});

// Get current settings
async function getSettings() {
  return await chrome.storage.sync.get({
    apiBase: CONFIG.DEFAULT_API_BASE,
    autoCheck: true,
    showSafeNotifications: true,
    notificationDuration: CONFIG.NOTIFICATION_DURATION,
    enableSounds: true
  });
}

// Extract hostname from URL
function extractHostname(inputUrl) {
  try {
    const url = new URL(inputUrl);
    return url.hostname.toLowerCase();
  } catch (_) {
    try { 
      return new URL('http://' + inputUrl).hostname.toLowerCase(); 
    } catch (e) { 
      return inputUrl.toLowerCase(); 
    }
  }
}

// Check if URL should be skipped
function shouldSkipUrl(url) {
  if (!url) return true;
  
  const skipPatterns = [
    /^chrome:/,
    /^edge:/,
    /^moz-extension:/,
    /^chrome-extension:/,
    /^about:/,
    /^file:/,
    /^data:/,
    /^blob:/,
    /^javascript:/,
    /^localhost/,
    /^127\.0\.0\.1/,
    /^192\.168\./,
    /^10\./,
    /^172\.(1[6-9]|2[0-9]|3[01])\./
  ];
  
  return skipPatterns.some(pattern => pattern.test(url));
}

// Check API health
async function checkApiHealth() {
  const now = Date.now();
  if (now - lastHealthCheck < 60000) return isApiHealthy; // Cache for 1 minute
  
  try {
    const { apiBase } = await getSettings();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${apiBase}/api/health`, {
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    isApiHealthy = response.ok;
    lastHealthCheck = now;
    
    // Update badge based on health
    await updateBadge(isApiHealthy ? 'ON' : 'OFF', isApiHealthy ? '#22c55e' : '#ef4444');
    
  } catch (error) {
    isApiHealthy = false;
    lastHealthCheck = now;
    await updateBadge('OFF', '#ef4444');
  }
  
  return isApiHealthy;
}

// Update extension badge
async function updateBadge(text, color) {
  try {
    await chrome.action.setBadgeText({ text });
    await chrome.action.setBadgeBackgroundColor({ color });
  } catch (error) {
    console.error('Failed to update badge:', error);
  }
}

// Main URL checking function
async function checkUrl(url, tabId = null) {
  if (shouldSkipUrl(url)) {
    return { 
      status: 'skipped', 
      reason: 'URL type not supported',
      url 
    };
  }
  
  const domain = extractHostname(url);
  const cacheKey = domain;
  
  // Check cache first
  const cached = urlCache.get(cacheKey);
  if (cached && (Date.now() - cached.timestamp) < CONFIG.CACHE_DURATION) {
    return { ...cached.result, fromCache: true };
  }
  
  // Check API health
  if (!await checkApiHealth()) {
    return {
      status: 'error',
      reason: 'API service unavailable',
      url,
      domain
    };
  }
  
  const { apiBase } = await getSettings();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CONFIG.CHECK_TIMEOUT);
  
  try {
    const response = await fetch(`${apiBase}/api/check-fast`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'User-Agent': 'PhishGuard-Pro/2.1-Extension'
      },
      body: JSON.stringify({ domain }),
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    const result = {
      status: 'success',
      data,
      url,
      domain,
      timestamp: Date.now(),
      statusCode: response.status
    };
    
    // Cache the result
    urlCache.set(cacheKey, {
      result,
      timestamp: Date.now()
    });
    
    // Clean old cache entries
    if (urlCache.size > 100) {
      const oldestKey = urlCache.keys().next().value;
      urlCache.delete(oldestKey);
    }
    
    return result;
    
  } catch (error) {
    clearTimeout(timeout);
    
    return {
      status: 'error',
      error: error.message,
      url,
      domain,
      timestamp: Date.now()
    };
  }
}

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) return;
  
  switch (message.type) {
    case 'CHECK_URL':
      if (message.url) {
        checkUrl(message.url, sender.tab?.id)
          .then(result => sendResponse({ success: true, result }))
          .catch(error => sendResponse({ 
            success: false, 
            error: error.message 
          }));
        return true; // Keep message channel open for async response
      }
      break;
      
    case 'GET_SETTINGS':
      getSettings()
        .then(settings => sendResponse({ success: true, settings }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;
      
    case 'UPDATE_SETTINGS':
      if (message.settings) {
        chrome.storage.sync.set(message.settings)
          .then(() => sendResponse({ success: true }))
          .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
      }
      break;
      
    case 'CLEAR_CACHE':
      urlCache.clear();
      sendResponse({ success: true, message: 'Cache cleared' });
      break;
      
    case 'GET_CACHE_STATS':
      sendResponse({
        success: true,
        stats: {
          size: urlCache.size,
          isApiHealthy,
          lastHealthCheck: new Date(lastHealthCheck).toISOString()
        }
      });
      break;
  }
});

// Handle tab updates for automatic checking
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const { autoCheck } = await getSettings();
    
    if (autoCheck && !shouldSkipUrl(tab.url)) {
      // Small delay to ensure content script is ready
      setTimeout(() => {
        chrome.tabs.sendMessage(tabId, {
          type: 'AUTO_CHECK',
          url: tab.url
        }).catch(() => {
          // Content script might not be ready yet, ignore error
        });
      }, 1000);
    }
  }
});

// Initialize health check on startup
checkApiHealth();

console.log('🛡️ Quanta AI background script loaded');
