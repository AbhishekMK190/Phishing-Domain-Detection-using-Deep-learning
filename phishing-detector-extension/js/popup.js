// Configuration
const API_URL = 'http://localhost:5000/api/check_fast';
let currentTab = null;

// DOM Elements
const statusElement = document.getElementById('status');
const urlElement = document.getElementById('url');
const predictionElement = document.getElementById('predictionResult');
const loaderElement = document.getElementById('loader');
const checkPageButton = document.getElementById('checkPage');
const reportFalsePositiveButton = document.getElementById('reportFalsePositive');
const reportPhishingButton = document.getElementById('reportPhishing');

// Update status display
function updateStatus(message, type = 'info') {
  statusElement.textContent = message;
  statusElement.className = `status ${type}`;
}

// Show loading state
function setLoading(isLoading) {
  loaderElement.style.display = isLoading ? 'block' : 'none';
  checkPageButton.disabled = isLoading;
  reportFalsePositiveButton.disabled = isLoading;
  reportPhishingButton.disabled = isLoading;
}

// Get current tab URL
async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Extract domain from URL
function extractDomain(url) {
  try {
    const domain = new URL(url).hostname.replace('www.', '');
    return domain;
  } catch (e) {
    console.error('Error extracting domain:', e);
    return null;
  }
}

// Check URL for phishing
async function checkUrl(url) {
  if (!url) {
    updateStatus('No URL provided', 'warning');
    return null;
  }

  const domain = extractDomain(url);
  if (!domain) {
    updateStatus('Invalid URL', 'warning');
    return null;
  }

  setLoading(true);
  updateStatus('Analyzing...', 'info');
  predictionElement.textContent = '';

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: domain }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error checking URL:', error);
    updateStatus('Error checking URL', 'danger');
    return null;
  } finally {
    setLoading(false);
  }
}

// Update UI with prediction result
function updatePredictionUI(result) {
  if (!result) return;

  const { is_phishing, confidence, message, features } = result;
  
  if (is_phishing) {
    updateStatus('⚠️ Phishing Detected!', 'danger');
    predictionElement.innerHTML = `
      <p>Confidence: ${(confidence * 100).toFixed(2)}%</p>
      <p>${message || 'This website appears to be a phishing site.'}</p>
      <p><strong>Warning:</strong> Do not enter any personal or sensitive information on this site.</p>
    `;
  } else {
    updateStatus('✅ Safe to Browse', 'safe');
    predictionElement.innerHTML = `
      <p>Confidence: ${(confidence * 100).toFixed(2)}%</p>
      <p>${message || 'This website appears to be safe.'}</p>
    `;
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', async () => {
  try {
    currentTab = await getCurrentTab();
    if (currentTab && currentTab.url) {
      urlElement.textContent = currentTab.url;
      const result = await checkUrl(currentTab.url);
      if (result) {
        updatePredictionUI(result);
      }
    } else {
      updateStatus('No active tab found', 'warning');
    }
  } catch (error) {
    console.error('Error initializing popup:', error);
    updateStatus('Error initializing extension', 'danger');
  }
});

checkPageButton.addEventListener('click', async () => {
  if (currentTab && currentTab.url) {
    const result = await checkUrl(currentTab.url);
    if (result) {
      updatePredictionUI(result);
    }
  }
});

reportFalsePositiveButton.addEventListener('click', async () => {
  if (currentTab && currentTab.url) {
    const domain = extractDomain(currentTab.url);
    if (confirm(`Report ${domain} as incorrectly flagged?`)) {
      try {
        const response = await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: domain,
            vote: 'false_positive',
            note: 'User reported as false positive'
          }),
        });
        
        if (response.ok) {
          alert('Thank you for your feedback! This helps improve the detection system.');
        } else {
          throw new Error('Failed to submit feedback');
        }
      } catch (error) {
        console.error('Error submitting feedback:', error);
        alert('Failed to submit feedback. Please try again later.');
      }
    }
  }
});

reportPhishingButton.addEventListener('click', async () => {
  if (currentTab && currentTab.url) {
    const domain = extractDomain(currentTab.url);
    if (confirm(`Report ${domain} as a phishing site?`)) {
      try {
        const response = await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: domain,
            vote: 'phishing',
            note: 'User reported as phishing site'
          }),
        });
        
        if (response.ok) {
          alert('Thank you for your report! Our team will review this site.');
        } else {
          throw new Error('Failed to submit report');
        }
      } catch (error) {
        console.error('Error submitting report:', error);
        alert('Failed to submit report. Please try again later.');
      }
    }
  }
});
