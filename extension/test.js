// PhishGuard Pro Extension Test Script
// Run this in the browser console to test the extension

console.log('🛡️ PhishGuard Pro Extension Test Starting...');

// Test 1: Check if extension is loaded
if (typeof chrome !== 'undefined' && chrome.runtime) {
  console.log('✅ Chrome extension API available');
  console.log('Extension ID:', chrome.runtime.id);
} else {
  console.error('❌ Chrome extension API not available');
}

// Test 2: Test API endpoints directly
async function testAPI() {
  console.log('\n🔍 Testing API endpoints...');
  
  try {
    // Test health endpoint
    console.log('Testing health endpoint...');
    const healthResponse = await fetch('http://127.0.0.1:5000/api/health');
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('✅ Health endpoint working:', healthData);
    } else {
      console.error('❌ Health endpoint failed:', healthResponse.status);
    }
    
    // Test check endpoint
    console.log('Testing check endpoint...');
    const checkResponse = await fetch('http://127.0.0.1:5000/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: 'google.com' })
    });
    
    if (checkResponse.ok) {
      const checkData = await checkResponse.json();
      console.log('✅ Check endpoint working:', checkData);
    } else {
      console.error('❌ Check endpoint failed:', checkResponse.status);
    }
    
  } catch (error) {
    console.error('❌ API test failed:', error);
  }
}

// Test 3: Test extension messaging
async function testExtensionMessaging() {
  console.log('\n📡 Testing extension messaging...');
  
  if (typeof chrome === 'undefined' || !chrome.runtime) {
    console.error('❌ Chrome extension API not available');
    return;
  }
  
  try {
    // Test settings message
    chrome.runtime.sendMessage({ type: 'GET_SETTINGS' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('❌ Settings message failed:', chrome.runtime.lastError);
      } else {
        console.log('✅ Settings message working:', response);
      }
    });
    
    // Test URL check message
    chrome.runtime.sendMessage({ 
      type: 'CHECK_URL', 
      url: 'https://google.com' 
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('❌ URL check message failed:', chrome.runtime.lastError);
      } else {
        console.log('✅ URL check message working:', response);
      }
    });
    
  } catch (error) {
    console.error('❌ Extension messaging test failed:', error);
  }
}

// Test 4: Check content script
function testContentScript() {
  console.log('\n📄 Testing content script...');
  
  // Check if PhishGuard content script is loaded
  if (typeof window.phishGuardCheck === 'function') {
    console.log('✅ Content script loaded');
    
    // Test manual check function
    try {
      window.phishGuardCheck();
      console.log('✅ Manual check function called');
    } catch (error) {
      console.error('❌ Manual check function failed:', error);
    }
  } else {
    console.error('❌ Content script not loaded or phishGuardCheck function not available');
  }
}

// Run all tests
async function runAllTests() {
  console.log('🧪 Running PhishGuard Pro Extension Tests...\n');
  
  await testAPI();
  await testExtensionMessaging();
  testContentScript();
  
  console.log('\n🏁 Test completed! Check results above.');
  console.log('If you see ❌ errors, those need to be fixed.');
  console.log('If you see ✅ success messages, those components are working.');
}

// Auto-run tests
runAllTests();
