document.addEventListener('DOMContentLoaded', async () => {
  // Get elements
  const phishingUrlElement = document.getElementById('phishing-url');
  const confidenceValueElement = document.getElementById('confidence-value');
  const confidenceLevelElement = document.getElementById('confidence-level');
  const warningMessageElement = document.getElementById('warning-message');
  const backToSafetyButton = document.getElementById('back-to-safety');
  const proceedAnywayButton = document.getElementById('proceed-anyway');
  const reportFalsePositiveLink = document.getElementById('report-false-positive');

  // Get the warning details from storage
  const data = await chrome.storage.local.get('warningDetails');
  const warningDetails = data.warningDetails;

  // Update the UI with warning details
  if (warningDetails) {
    phishingUrlElement.textContent = warningDetails.domain || 'this website';
    
    // Animate the confidence meter
    const confidence = Math.round((warningDetails.confidence || 0.7) * 100);
    confidenceValueElement.textContent = confidence;
    
    // Animate the confidence level bar
    setTimeout(() => {
      confidenceLevelElement.style.width = `${confidence}%`;
    }, 100);

    // Update the warning message
    if (warningDetails.message) {
      warningMessageElement.textContent = warningDetails.message;
    }

    // Set up the back to safety button
    backToSafetyButton.addEventListener('click', () => {
      // Go to a safe page (e.g., Google or the extension's homepage)
      window.location.href = 'https://www.google.com';
    });

    // Set up the proceed anyway button
    proceedAnywayButton.addEventListener('click', () => {
      // Store user's preference to not show the warning again for this site
      chrome.storage.local.get('ignoredWarnings', (data) => {
        const ignoredWarnings = data.ignoredWarnings || [];
        ignoredWarnings.push(warningDetails.domain);
        chrome.storage.local.set({ ignoredWarnings });
        
        // Navigate to the original URL
        window.location.href = warningDetails.url;
      });
    });

    // Set up the report false positive link
    reportFalsePositiveLink.addEventListener('click', async (e) => {
      e.preventDefault();
      
      try {
        const response = await fetch('http://localhost:5000/api/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: warningDetails.domain,
            vote: 'false_positive',
            note: 'User reported as false positive from warning page'
          }),
        });
        
        if (response.ok) {
          alert('Thank you for your feedback! This helps improve our detection system.');
        } else {
          throw new Error('Failed to submit feedback');
        }
      } catch (error) {
        console.error('Error submitting feedback:', error);
        alert('Failed to submit feedback. Please try again later.');
      }
    });
  } else {
    // If no warning details are found, show a generic message
    phishingUrlElement.textContent = 'this website';
    warningMessageElement.textContent = 'This website has been flagged as potentially dangerous.';
    
    // Set default confidence
    confidenceValueElement.textContent = '85';
    confidenceLevelElement.style.width = '85%';
    
    // Just go back to safety if no details are available
    backToSafetyButton.addEventListener('click', () => {
      window.location.href = 'https://www.google.com';
    });
    
    // Hide the proceed button if no details are available
    proceedAnywayButton.style.display = 'none';
  }
});
