// PhishGuard Pro - Enhanced Content Script with Auto-Popup
(() => {
  'use strict';
  
  // Configuration
  const CONFIG = {
    NOTIFICATION_ID: 'phishguard-notification',
    CHECK_DELAY: 1500,
    AUTO_HIDE_SAFE: 4000,
    AUTO_HIDE_WARNING: 8000,
    PHISHING_PERSISTENT: true
  };
  
  // State management
  let currentNotification = null;
  let lastUrl = location.href;
  let isChecking = false;
  let settings = {
    autoCheck: true,
    showSafeNotifications: true,
    notificationDuration: 8000,
    enableSounds: true
  };
  
  // Initialize
  init();
  
  async function init() {
    console.log('🛡️ PhishGuard Pro content script loaded');
    
    // Load settings
    await loadSettings();
    
    // Set up URL monitoring for SPAs
    setupUrlMonitoring();
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener(handleMessage);
    
    // Initial check after a short delay
    setTimeout(() => {
      if (settings.autoCheck) {
        console.log('🔍 Starting initial auto-check for:', location.href);
        performCheck(location.href, 'auto');
      }
    }, 2000);
  }
  
  // Load settings from storage
  async function loadSettings() {
    try {
      const response = await sendMessage({ type: 'GET_SETTINGS' });
      if (response.success) {
        settings = { ...settings, ...response.settings };
      }
    } catch (error) {
      console.warn('Failed to load settings:', error);
    }
  }
  
  // Handle messages from background script
  function handleMessage(message, sender, sendResponse) {
    if (!message || !message.type) return;
    
    switch (message.type) {
      case 'AUTO_CHECK':
        if (message.url && settings.autoCheck) {
          console.log('🔍 Received AUTO_CHECK message for:', message.url);
          performCheck(message.url, 'auto');
        }
        break;
        
      case 'MANUAL_CHECK':
        performCheck(location.href, 'manual');
        break;
        
      case 'UPDATE_SETTINGS':
        if (message.settings) {
          settings = { ...settings, ...message.settings };
        }
        break;
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
  
  // Set up URL monitoring for Single Page Applications
  function setupUrlMonitoring() {
    // Monitor URL changes
    setInterval(() => {
      if (lastUrl !== location.href) {
        lastUrl = location.href;
        if (settings.autoCheck) {
          console.log('🔍 URL changed, performing auto-check for:', location.href);
          setTimeout(() => performCheck(location.href, 'auto'), 500);
        }
      }
    }, CONFIG.CHECK_DELAY);
    
    // Monitor pushState/replaceState
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
      originalPushState.apply(this, args);
      if (settings.autoCheck) {
        console.log('🔍 pushState detected, performing auto-check for:', location.href);
        setTimeout(() => performCheck(location.href, 'auto'), 500);
      }
    };
    
    history.replaceState = function(...args) {
      originalReplaceState.apply(this, args);
      if (settings.autoCheck) {
        console.log('🔍 replaceState detected, performing auto-check for:', location.href);
        setTimeout(() => performCheck(location.href, 'auto'), 500);
      }
    };
    
    // Monitor popstate events
    window.addEventListener('popstate', () => {
      if (settings.autoCheck) {
        console.log('🔍 popstate detected, performing auto-check for:', location.href);
        setTimeout(() => performCheck(location.href, 'auto'), 500);
      }
    });
  }
  
  // Perform security check
  async function performCheck(url, trigger = 'manual') {
    if (isChecking || !url) return;
    
    isChecking = true;
    
    try {
      // Always show loading notification for auto checks too
      showNotification({
        type: 'loading',
        domain: extractDomain(url),
        message: 'Checking website security...',
        trigger
      });
      
      // Try direct API call first (more reliable)
      const domain = extractDomain(url);
      console.log(`🔍 Direct API check for domain: ${domain}`);
      
      try {
        const response = await fetch('http://127.0.0.1:5000/api/check-fast', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'PhishGuard-Content-Script/2.1'
          },
          body: JSON.stringify({ domain: domain }),
          signal: AbortSignal.timeout(8000)
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('🔍 Direct API response:', data);
          
          handleCheckResult({
            status: 'success',
            data: data,
            domain: domain,
            url: url,
            fromCache: data.cached || false
          }, trigger);
          
          return; // Success, exit early
        }
      } catch (directError) {
        console.log('🔍 Direct API failed, trying background script:', directError.message);
      }
      
      // Fallback to background script
      const response = await sendMessage({
        type: 'CHECK_URL',
        url: url
      });
      
      if (response.success && response.result) {
        handleCheckResult(response.result, trigger);
      } else {
        handleCheckError(response.error || 'Unknown error', trigger);
      }
      
    } catch (error) {
      handleCheckError(error.message, trigger);
    } finally {
      isChecking = false;
    }
  }
  
  // Handle check result
  function handleCheckResult(result, trigger) {
    console.log('🔍 Handling check result:', result, 'trigger:', trigger);
    
    if (result.status === 'skipped') {
      // Don't show notifications for skipped URLs
      return;
    }
    
    if (result.status === 'success' && result.data) {
      const data = result.data;
      
      if (data.status === 'ok') {
        const isPhishing = data.label === 'phishing';
        const score = parseFloat(data.score || 0);
        
        console.log(`🔍 Result: ${data.label}, Score: ${score}, Phishing: ${isPhishing}`);
        
        // Determine notification type
        let type, message;
        if (isPhishing) {
          type = 'danger';
          message = '🚨 PHISHING DETECTED - This website may be dangerous!';
        } else if (score > 0.3) {
          type = 'warning';
          message = '⚠️ This website has suspicious characteristics';
        } else {
          type = 'safe';
          message = '✅ This website appears to be safe';
        }
        
        console.log(`🔍 Showing ${type} notification for ${result.domain}`);
        
        // Always show notifications for auto checks (when user visits a page)
        // Show based on settings for manual checks
        const shouldShow = trigger === 'auto' || 
                          isPhishing || 
                          type === 'warning' || 
                          settings.showSafeNotifications;
        
        if (shouldShow) {
          showNotification({
            type,
            domain: result.domain || extractDomain(location.href),
            message,
            score: score.toFixed(3),
            trigger,
            fromCache: result.fromCache
          });
        }
        
        // Play sound if enabled
        if (settings.enableSounds && (isPhishing || type === 'warning')) {
          playNotificationSound(type);
        }
        
      } else {
        // Handle API errors
        console.log('🔍 API error:', data.detail || 'API returned an error');
        if (trigger === 'manual') {
          handleCheckError(data.detail || 'API returned an error', trigger);
        }
      }
    } else {
      console.log('🔍 Check failed:', result.error || 'Check failed');
      if (trigger === 'manual') {
        handleCheckError(result.error || 'Check failed', trigger);
      }
    }
  }
  
  // Handle check errors
  function handleCheckError(error, trigger) {
    if (trigger === 'manual') {
      showNotification({
        type: 'warning',
        domain: extractDomain(location.href),
        message: '⚠️ Unable to verify website security',
        details: error,
        trigger
      });
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
  
  // Show notification popup
  function showNotification(options) {
    removeExistingNotification();
    
    const notification = createNotificationElement(options);
    document.documentElement.appendChild(notification);
    currentNotification = notification;
    
    // Auto-hide based on type
    let autoHideDelay;
    switch (options.type) {
      case 'safe':
        autoHideDelay = CONFIG.AUTO_HIDE_SAFE;
        break;
      case 'warning':
        autoHideDelay = CONFIG.AUTO_HIDE_WARNING;
        break;
      case 'danger':
        if (!CONFIG.PHISHING_PERSISTENT) {
          autoHideDelay = settings.notificationDuration;
        }
        break;
      case 'loading':
        autoHideDelay = 10000; // 10 seconds max for loading
        break;
      default:
        autoHideDelay = settings.notificationDuration;
    }
    
    if (autoHideDelay) {
      setTimeout(() => {
        removeNotification(notification);
      }, autoHideDelay);
    }
  }
  
  // Create notification element
  function createNotificationElement(options) {
    const notification = document.createElement('div');
    notification.id = CONFIG.NOTIFICATION_ID;
    notification.className = `phishguard-${options.type}`;
    
    // Header
    const header = document.createElement('div');
    header.className = 'phishguard-header';
    
    const title = document.createElement('div');
    title.className = 'phishguard-title';
    
    const icon = document.createElement('span');
    icon.className = 'phishguard-icon';
    
    switch (options.type) {
      case 'safe':
        icon.textContent = '🛡️';
        title.appendChild(icon);
        title.appendChild(document.createTextNode('PhishGuard Pro'));
        break;
      case 'warning':
        icon.textContent = '⚠️';
        title.appendChild(icon);
        title.appendChild(document.createTextNode('Security Warning'));
        break;
      case 'danger':
        icon.textContent = '🚨';
        title.appendChild(icon);
        title.appendChild(document.createTextNode('PHISHING DETECTED'));
        break;
      case 'loading':
        icon.textContent = '🔍';
        title.appendChild(icon);
        title.appendChild(document.createTextNode('Scanning...'));
        break;
      default:
        icon.textContent = '🛡️';
        title.appendChild(icon);
        title.appendChild(document.createTextNode('PhishGuard Pro'));
    }
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'phishguard-close';
    closeBtn.textContent = '×';
    closeBtn.setAttribute('aria-label', 'Close notification');
    closeBtn.onclick = () => removeNotification(notification);
    
    header.appendChild(title);
    header.appendChild(closeBtn);
    
    // Content
    const content = document.createElement('div');
    content.className = 'phishguard-content';
    
    if (options.domain) {
      const domain = document.createElement('div');
      domain.className = 'phishguard-domain';
      domain.textContent = options.domain;
      content.appendChild(domain);
    }
    
    const message = document.createElement('div');
    message.className = 'phishguard-message';
    message.textContent = options.message;
    content.appendChild(message);
    
    if (options.score || options.details || options.fromCache) {
      const details = document.createElement('div');
      details.className = 'phishguard-details';
      
      if (options.score) {
        const score = document.createElement('span');
        score.className = 'phishguard-score';
        score.textContent = `Risk Score: ${options.score}`;
        details.appendChild(score);
      }
      
      if (options.details) {
        const detailText = document.createElement('span');
        detailText.textContent = options.details;
        details.appendChild(detailText);
      }
      
      const time = document.createElement('span');
      time.className = 'phishguard-time';
      time.textContent = options.fromCache ? 'Cached result' : 'Just checked';
      details.appendChild(time);
      
      content.appendChild(details);
    }
    
    // Add progress bar for loading
    if (options.type === 'loading') {
      const progress = document.createElement('div');
      progress.className = 'phishguard-progress';
      const progressBar = document.createElement('div');
      progressBar.className = 'phishguard-progress-bar';
      progress.appendChild(progressBar);
      content.appendChild(progress);
    }
    
    // Add action buttons for phishing
    if (options.type === 'danger') {
      const actions = document.createElement('div');
      actions.className = 'phishguard-actions';
      
      const reportBtn = document.createElement('button');
      reportBtn.className = 'phishguard-btn';
      reportBtn.textContent = 'Report False Positive';
      reportBtn.onclick = () => reportFalsePositive(options.domain);
      
      const leaveBtn = document.createElement('button');
      leaveBtn.className = 'phishguard-btn phishguard-btn-primary';
      leaveBtn.textContent = 'Leave This Site';
      leaveBtn.onclick = () => window.history.back();
      
      actions.appendChild(reportBtn);
      actions.appendChild(leaveBtn);
      content.appendChild(actions);
    }
    
    notification.appendChild(header);
    notification.appendChild(content);
    
    return notification;
  }
  
  // Remove existing notification
  function removeExistingNotification() {
    const existing = document.getElementById(CONFIG.NOTIFICATION_ID);
    if (existing) {
      removeNotification(existing);
    }
  }
  
  // Remove notification with animation
  function removeNotification(notification) {
    if (!notification || !notification.parentNode) return;
    
    notification.style.animation = 'phishguard-slide-out 0.3s cubic-bezier(0.4, 0, 1, 1)';
    
    setTimeout(() => {
      try {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
        if (currentNotification === notification) {
          currentNotification = null;
        }
      } catch (error) {
        // Ignore errors during cleanup
      }
    }, 300);
  }
  
  // Play notification sound
  function playNotificationSound(type) {
    try {
      // Create audio context for sound
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Different sounds for different types
      if (type === 'danger') {
        // Urgent warning sound
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
      } else {
        // Gentle warning sound
        oscillator.frequency.setValueAtTime(500, audioContext.currentTime);
      }
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      // Sound failed, ignore
    }
  }
  
  // Report false positive
  function reportFalsePositive(domain) {
    // This would integrate with your feedback system
    console.log('Reporting false positive for:', domain);
    
    // Show confirmation
    showNotification({
      type: 'safe',
      domain: domain,
      message: '✅ Thank you! Your feedback has been recorded.',
      trigger: 'feedback'
    });
  }
  
  // Expose global function for manual checking
  window.phishGuardCheck = () => {
    performCheck(location.href, 'manual');
  };
  
  console.log('🛡️ PhishGuard Pro content script ready');
})();
