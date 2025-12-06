# Extension Troubleshooting Guide

## ✅ Server Status: WORKING
- Flask server is running on port 5000
- API endpoints `/api/health` and `/api/check` are responding correctly
- CORS is properly configured to allow all origins

## 🔧 Extension Issues to Check:

### 1. **Browser Extension Loading**
- Make sure you're loading the extension as an **unpacked extension**
- Go to `chrome://extensions/` or `edge://extensions/`
- Enable **Developer mode** (toggle in top-right)
- Click **"Load unpacked"** and select the `extension` folder
- Look for any error messages in the extension console

### 2. **Manifest Version Issues**
Your extension uses Manifest V3. Make sure:
- You're using a recent version of Chrome/Edge (90+)
- No syntax errors in `manifest.json`

### 3. **CORS and Network Issues**
The extension popup makes direct fetch requests to:
```
http://127.0.0.1:5000/api/check
```

### 4. **Test the Extension**
1. Load the extension as unpacked
2. Open any website
3. Click the extension icon in the toolbar
4. You should see the popup with API status

### 5. **Debug Steps**
1. Open Chrome DevTools (F12)
2. Go to the Console tab
3. Look for any JavaScript errors
4. Check the Network tab to see if API requests are being made

### 6. **If Still Not Working**
- Try opening `test_api.html` in your browser
- This will test if the API connection works from a regular webpage
- If it works, the issue is with the extension, not the server

## 🚀 **Quick Test Commands:**

```bash
# Test API directly
python -c "import requests; r=requests.post('http://127.0.0.1:5000/api/check', json={'domain':'google.com'}); print('Status:', r.status_code)"

# Check if Flask is running
python -c "import requests; r=requests.get('http://127.0.0.1:5000/api/health'); print('Health:', r.status_code)"
```

## 📝 **Common Issues:**

1. **Firewall blocking port 5000**
2. **Flask server not running on the expected port**
3. **Extension not loaded properly in developer mode**
4. **CORS issues (though these should be fixed)**
5. **Browser security restrictions**

## 🎯 **Next Steps:**

1. **Confirm the extension loads** in Chrome/Edge developer mode
2. **Check browser console** for JavaScript errors
3. **Verify API connectivity** using the test file
4. **Check Flask server logs** for any error messages

The Flask server is definitely working correctly. The issue is likely with the browser extension loading or configuration.
