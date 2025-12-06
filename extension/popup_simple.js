// Quanta AI - Simplified Popup Script
(() => {
  'use strict';
  
  console.log('🛡️ Quanta AI popup loading...');
  
  // DOM elements
  const statusCircle = document.getElementById('statusCircle');
  const domainName = document.getElementById('domainName');
  const domainStatus = document.getElementById('domainStatus');
  const scoreInfo = document.getElementById('scoreInfo');
  const actions = document.getElementById('actions');
  const recheckBtn = document.getElementById('recheckBtn');
  const reportBtn = document.getElementById('reportBtn');
  const errorMessage = document.getElementById('errorMessage');
  const errorDetail = document.getElementById('errorDetail');
  const apiStatus = document.getElementById('apiStatus');
  
  let currentTab = null;
  
  // Initialize
  init();
  
  async function init() {
    console.log('Initializing popup...');
    
    // Set up event listeners
    recheckBtn.addEventListener('click', () => performCheck(true));
    reportBtn.addEventListener('click', () => reportIssue());
    
    // Get current tab
    await getCurrentTab();
    
    // Start checking
    await performCheck();
  }
  
  // Get current active tab
  async function getCurrentTab() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      currentTab = tab;
      
      if (tab && tab.url) {
        const domain = extractDomain(tab.url);
        domainName.textContent = domain || 'Unknown domain';
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
      
      console.log('Check response:', response);
      
      if (response.success && response.result) {
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
    
    console.log('Handling result:', result);
    
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
        domainName.textContent = result.domain || extractDomain(currentTab.url);
        
        // Show result
        if (isPhishing) {
          showDangerResult(score, result.fromCache);
        } else if (score > 0.3) {
          showWarningResult(score, result.fromCache);
        } else {
          showSafeResult(score, result.fromCache);
        }
        
        // Show actions
        actions.style.display = 'flex';
        
      } else {
        handleCheckError(data.detail || 'API returned an error');
      }
    } else if (result.status === 'error') {
      handleCheckError(result.error || result.reason || 'Check failed');
    } else {
      handleCheckError('Unknown response format');
    }
    
    // Update API status
    apiStatus.textContent = 'API Status: Connected';
  }
  
  // Handle check error
  function handleCheckError(error) {
    console.error('Check error:', error);
    
    statusCircle.className = 'status-circle offline';
    statusCircle.innerHTML = '⚠️';
    
    domainStatus.textContent = 'Unable to verify security';
    scoreInfo.textContent = '';
    
    showError(error);
    
    apiStatus.textContent = 'API Status: Offline';
    actions.style.display = 'flex';
    reportBtn.textContent = 'Report Problem';
  }
  
  // Show loading state
  function showLoading() {
    statusCircle.className = 'status-circle loading';
    statusCircle.innerHTML = '<div class="spinner"></div>';
    
    domainStatus.textContent = 'Checking security...';
    scoreInfo.textContent = '';
    actions.style.display = 'none';
    hideError();
  }
  
  // Show safe result
  function showSafeResult(score, fromCache) {
    statusCircle.className = 'status-circle safe';
    statusCircle.innerHTML = '✅';
    
    domainStatus.textContent = 'This website appears to be safe';
    scoreInfo.textContent = `Risk Score: ${score.toFixed(3)} ${fromCache ? '(cached)' : ''}`;
  }
  
  // Show warning result
  function showWarningResult(score, fromCache) {
    statusCircle.className = 'status-circle warning';
    statusCircle.innerHTML = '⚠️';
    
    domainStatus.textContent = 'This website has suspicious characteristics';
    scoreInfo.textContent = `Risk Score: ${score.toFixed(3)} ${fromCache ? '(cached)' : ''}`;
  }
  
  // Show danger result
  function showDangerResult(score, fromCache) {
    statusCircle.className = 'status-circle danger';
    statusCircle.innerHTML = '🚨';
    
    domainStatus.textContent = 'PHISHING DETECTED - This may be dangerous!';
    scoreInfo.textContent = `Risk Score: ${score.toFixed(3)} ${fromCache ? '(cached)' : ''}`;
    
    reportBtn.textContent = 'Report False Positive';
  }
  
  // Show unsupported tab
  function showUnsupportedTab() {
    statusCircle.className = 'status-circle offline';
    statusCircle.innerHTML = '🚫';
    
    domainName.textContent = 'System Page';
    domainStatus.textContent = 'This page type is not supported';
    scoreInfo.textContent = '';
    actions.style.display = 'none';
    hideError();
  }
  
  // Show error message
  function showError(message) {
    errorMessage.style.display = 'block';
    errorDetail.textContent = message;
  }
  
  // Hide error message
  function hideError() {
    errorMessage.style.display = 'none';
  }
  
  // Report issue
  function reportIssue() {
    console.log('Reporting issue for:', currentTab?.url);
    
    domainStatus.textContent = 'Thank you for your feedback!';
    reportBtn.textContent = 'Reported ✓';
    reportBtn.disabled = true;
    
    setTimeout(() => {
      reportBtn.disabled = false;
      reportBtn.textContent = 'Report';
    }, 3000);
  }
  
  console.log('🛡️ Quanta AI popup ready');
})();
