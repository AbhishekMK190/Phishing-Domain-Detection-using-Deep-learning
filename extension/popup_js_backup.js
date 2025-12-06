// PhishGuard Pro - Modern Popup Interface
(() => {
  'use strict';
  
  // DOM elements
  const elements = {
    statusCircle: document.getElementById('statusCircle'),
    domainName: document.getElementById('domainName'),
    domainStatus: document.getElementById('domainStatus'),
    scoreInfo: document.getElementById('scoreInfo'),
    actions: document.getElementById('actions'),
    recheckBtn: document.getElementById('recheckBtn'),
    reportBtn: document.getElementById('reportBtn'),
    errorMessage: document.getElementById('errorMessage'),
    errorDetail: document.getElementById('errorDetail'),
    statusDot: document.getElementById('statusDot'),
    apiStatusText: document.getElementById('apiStatusText'),
    cacheInfo: document.getElementById('cacheInfo'),
    settingsLink: document.getElementById('settingsLink')
  };
  
  // State
  let currentTab = null;
  let lastCheckResult = null;
  let settings = {};
  
  // Initialize popup
  init();
  
  async function init() {
    console.log('🛡️ Quanta AI popup initializing...');
    
    // Set up event listeners
    setupEventListeners();
    
    // Load settings and current tab
    await Promise.all([
      loadSettings(),
      getCurrentTab()
    ]);
    
    // Start checking
    await performCheck();
    
    // Update cache info
    updateCacheInfo();
  }
  
  // Set up event listeners
  function setupEventListeners() {
    elements.recheckBtn.addEventListener('click', () => {
      performCheck(true);
    });
    
    elements.reportBtn.addEventListener('click', () => {
      reportIssue();
    });
    
    elements.settingsLink.addEventListener('click', (e) => {
      e.preventDefault();
      openOptionsPage();
    });
  }
  
  // Load settings from storage
  async function loadSettings() {
    try {
      const response = await sendMessage({ type: 'GET_SETTINGS' });
      if (response.success) {
        settings = response.settings;
      }
    } catch (error) {
      console.warn('Failed to load settings:', error);
    }
  }
  
  // Get current active tab
  async function getCurrentTab() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      currentTab = tab;
      
      if (tab && tab.url) {
        const domain = extractDomain(tab.url);
        elements.domainName.textContent = domain || 'Unknown domain';
      }
    } catch (error) {
      console.error('Failed to get current tab:', error);
      showError('Unable to access current tab');
    }
  }
  
  // Extract domain from URL
  function extractDomain(url) {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
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
  
  // Perform security check
  async function performCheck(force = false) {
    if (!currentTab || !currentTab.url) {
      showError('No active tab found');
      return;
    }
    
    const url = currentTab.url;
    
    // Check if URL should be skipped
    if (shouldSkipUrl(url)) {
      showUnsupportedTab();
      return;
    }
    
    // Show loading state
    showLoading();
    
    try {
      // Send check request
      const response = await sendMessage({
        type: 'CHECK_URL',
        url: url
      });
      
      if (response.success && response.result) {
        lastCheckResult = response.result;
        handleCheckResult(response.result);
      } else {
        handleCheckError(response.error || 'Check failed');
      }
      
    } catch (error) {
      handleCheckError(error.message);
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
      /^data:/
    ];
    
    return skipPatterns.some(pattern => pattern.test(url));
  }
  
  // Handle check result
  function handleCheckResult(result) {
    hideError();
    
    if (result.status === 'skipped') {
      showUnsupportedTab();
      return;
    }
    
    if (result.status === 'success' && result.data) {
      const data = result.data;
      
      if (data.status === 'ok') {
        const isPhishing = data.label === 'phishing';
        const score = parseFloat(data.score || 0);
        
        // Update domain info
        elements.domainName.textContent = result.domain || 'Unknown domain';
        
        // Determine status and show result
        if (isPhishing) {
          showDangerResult(score, result.fromCache);
        } else if (score > 0.3) {
          showWarningResult(score, result.fromCache);
        } else {
          showSafeResult(score, result.fromCache);
        }
        
        // Show actions
        elements.actions.style.display = 'flex';
        
      } else {
        handleCheckError(data.detail || 'API returned an error');
      }
    } else if (result.status === 'error') {
      handleCheckError(result.error || result.reason || 'Check failed');
    } else {
      handleCheckError('Unknown response format');
    }
    
    // Update API status
    updateApiStatus(true);
  }
  
  // Handle check error
  function handleCheckError(error) {
    console.error('Check error:', error);
    
    // Update UI
    elements.statusCircle.className = 'status-circle offline';
    elements.statusCircle.innerHTML = `
      <div class="status-text">
        <div class="status-icon">⚠️</div>
        <div>Check Failed</div>
      </div>
    `;
    
    elements.domainStatus.textContent = 'Unable to verify security';
    elements.scoreInfo.textContent = '';
    
    // Show error details
    showError(error);
    
    // Update API status
    updateApiStatus(false);
    
    // Show recheck action
    elements.actions.style.display = 'flex';
    elements.reportBtn.textContent = 'Report Problem';
  }
  
  // Show loading state
  function showLoading() {
    elements.statusCircle.className = 'status-circle loading';
    elements.statusCircle.innerHTML = '<div class="spinner"></div>';
    
    elements.domainStatus.textContent = 'Checking security...';
    elements.scoreInfo.textContent = '';
    elements.actions.style.display = 'none';
    hideError();
  }
  
  // Show safe result
  function showSafeResult(score, fromCache) {
    elements.statusCircle.className = 'status-circle safe';
    elements.statusCircle.innerHTML = `
      <div class="status-text">
        <div class="status-icon">✅</div>
        <div>Safe Website</div>
      </div>
    `;
    
    elements.domainStatus.textContent = 'This website appears to be legitimate';
    elements.scoreInfo.textContent = `Risk Score: ${score.toFixed(3)} ${fromCache ? '(cached)' : ''}`;
  }
  
  // Show warning result
  function showWarningResult(score, fromCache) {
    elements.statusCircle.className = 'status-circle warning';
    elements.statusCircle.innerHTML = `
      <div class="status-text">
        <div class="status-icon">⚠️</div>
        <div>Suspicious</div>
      </div>
    `;
    
    elements.domainStatus.textContent = 'This website has suspicious characteristics';
    elements.scoreInfo.textContent = `Risk Score: ${score.toFixed(3)} ${fromCache ? '(cached)' : ''}`;
  }
  
  // Show danger result
  function showDangerResult(score, fromCache) {
    elements.statusCircle.className = 'status-circle danger';
    elements.statusCircle.innerHTML = `
      <div class="status-text">
        <div class="status-icon">🚨</div>
        <div>PHISHING DETECTED</div>
      </div>
    `;
    
    elements.domainStatus.textContent = 'This website may be a phishing attempt!';
    elements.scoreInfo.textContent = `Risk Score: ${score.toFixed(3)} ${fromCache ? '(cached)' : ''}`;
    
    // Change button text for phishing
    elements.reportBtn.textContent = 'Report False Positive';
  }
  
  // Show unsupported tab
  function showUnsupportedTab() {
    elements.statusCircle.className = 'status-circle offline';
    elements.statusCircle.innerHTML = `
      <div class="status-text">
        <div class="status-icon">🚫</div>
        <div>Unsupported</div>
      </div>
    `;
    
    elements.domainName.textContent = 'System Page';
    elements.domainStatus.textContent = 'This page type is not supported';
    elements.scoreInfo.textContent = '';
    elements.actions.style.display = 'none';
    hideError();
  }
  
  // Show error message
  function showError(message) {
    elements.errorMessage.style.display = 'block';
    elements.errorDetail.textContent = message;
  }
  
  // Hide error message
  function hideError() {
    elements.errorMessage.style.display = 'none';
  }
  
  // Update API status indicator
  function updateApiStatus(isOnline) {
    if (isOnline) {
      elements.statusDot.className = 'status-dot';
      elements.apiStatusText.textContent = 'API Connected';
    } else {
      elements.statusDot.className = 'status-dot offline';
      elements.apiStatusText.textContent = 'API Offline';
    }
  }
  
  // Update cache information
  async function updateCacheInfo() {
    try {
      const response = await sendMessage({ type: 'GET_CACHE_STATS' });
      if (response.success && response.stats) {
        const stats = response.stats;
        elements.cacheInfo.textContent = `Cache: ${stats.size} entries`;
      }
    } catch (error) {
      // Ignore cache info errors
    }
  }
  
  // Report issue or false positive
  function reportIssue() {
    if (!currentTab || !lastCheckResult) return;
    
    const domain = extractDomain(currentTab.url);
    
    // This would integrate with your feedback system
    console.log('Reporting issue for domain:', domain);
    
    // Show confirmation
    elements.domainStatus.textContent = 'Thank you for your feedback!';
    elements.reportBtn.textContent = 'Reported ✓';
    elements.reportBtn.disabled = true;
    
    // Re-enable after 3 seconds
    setTimeout(() => {
      elements.reportBtn.disabled = false;
      elements.reportBtn.textContent = lastCheckResult.data?.label === 'phishing' ? 'Report False Positive' : 'Report Issue';
    }, 3000);
  }
  
  // Open options page
  function openOptionsPage() {
    chrome.runtime.openOptionsPage();
    window.close();
  }
  
  console.log('🛡️ Quanta AI popup ready');
})();
