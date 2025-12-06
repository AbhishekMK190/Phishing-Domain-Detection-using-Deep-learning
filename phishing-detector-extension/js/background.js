// Listen for tab updates to check for phishing when a page loads
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  // Only proceed if the page has finished loading and has a URL
  if (changeInfo.status === 'complete' && tab.url) {
    try {
      const domain = new URL(tab.url).hostname.replace('www.', '');
      
      // Skip checking certain URLs
      if (tab.url.startsWith('chrome://') || 
          tab.url.startsWith('edge://') || 
          tab.url.startsWith('about:') ||
          tab.url.startsWith('chrome-extension://')) {
        return;
      }

      // Check the URL using the API
      const response = await fetch('http://localhost:5000/api/check_fast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: domain }),
      });

      if (response.ok) {
        const result = await response.json();
        
        // If phishing detected, show a warning page
        if (result.is_phishing) {
          // Store the warning details in chrome.storage
          await chrome.storage.local.set({
            warningDetails: {
              url: tab.url,
              domain: domain,
              confidence: result.confidence,
              message: result.message || 'This website has been identified as a potential phishing site.'
            }
          });
          
          // Redirect to the warning page
          await chrome.tabs.update(tabId, {
            url: chrome.runtime.getURL('warning.html')
          });
        }
      }
    } catch (error) {
      console.error('Background check error:', error);
    }
  }
});

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkUrl') {
    checkUrl(request.url)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Required for async sendResponse
  }
});

// Function to check URL (used by both background and message listener)
async function checkUrl(url) {
  try {
    const domain = new URL(url).hostname.replace('www.', '');
    const response = await fetch('http://localhost:5000/api/check_fast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: domain }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error checking URL:', error);
    return { error: error.message };
  }
}
