# 🛡️ Extension Troubleshooting Guide

## Quick Fix Steps

### 1. **Check Flask API Server**
- Make sure the Flask app is running: `python app.py`
- Verify API is accessible: Open http://127.0.0.1:5000/api/health
- You should see: `{"status": "ok", "message": "PhishGuard API is running"}`

### 2. **Reload Extension**
1. Open Chrome/Edge and go to `chrome://extensions/` or `edge://extensions/`
2. Find "🛡️ Quanta AI" extension
3. Click the **Reload** button (circular arrow icon)
4. Check if there are any errors in the extension details

### 3. **Check Extension Permissions**
- Ensure the extension has these permissions:
  - ✅ Read and change all your data on all websites
  - ✅ Display notifications
  - ✅ Access to localhost:5000

### 4. **Debug Extension Issues**

#### Open Extension Console:
1. Right-click the extension icon → "Inspect popup"
2. Check Console tab for errors
3. Look for red error messages

#### Common Error Messages and Fixes:

**"Loading loading..."**
- ❌ API server not running
- ✅ Fix: Run `python app.py` in project directory

**"Extension context invalidated"**
- ❌ Extension was reloaded while popup was open
- ✅ Fix: Close popup and reopen

**"Failed to fetch"**
- ❌ CORS or network issue
- ✅ Fix: Check if Flask app allows CORS (it should)

**"No response from background script"**
- ❌ Background script crashed
- ✅ Fix: Reload extension

### 5. **Test Extension Manually**

#### Test API Connection:
```javascript
// Paste this in browser console on any webpage:
fetch('http://127.0.0.1:5000/api/check', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({domain: 'google.com'})
})
.then(r => r.json())
.then(console.log)
```

#### Expected Response:
```json
{
  "status": "ok",
  "domain": "google.com",
  "label": "legitimate",
  "score": 0.0,
  "trusted": true
}
```

### 6. **Extension Installation Steps**

1. **Load Extension:**
   - Open `chrome://extensions/`
   - Enable "Developer mode" (top right)
   - Click "Load unpacked"
   - Select the `extension` folder

2. **Pin Extension:**
   - Click the puzzle piece icon in toolbar
   - Click the pin icon next to "🛡️ Quanta AI"

### 7. **Current Status Check**

✅ **Flask API**: Running on http://127.0.0.1:5000
✅ **Health Endpoint**: /api/health working
✅ **Check Endpoint**: /api/check working
✅ **Extension Files**: Updated with better error handling

### 8. **If Still Not Working**

1. **Check Browser Console:**
   - Press F12 → Console tab
   - Look for error messages

2. **Try Different Browser:**
   - Test in Chrome vs Edge
   - Some browsers handle extensions differently

3. **Restart Everything:**
   - Close browser completely
   - Stop Flask app (Ctrl+C)
   - Restart Flask app: `python app.py`
   - Restart browser and test extension

### 9. **Extension Popup Should Show:**

- 🟢 **Green Circle**: Website is safe
- 🟡 **Yellow Circle**: Suspicious website  
- 🔴 **Red Circle**: Phishing detected
- ⚫ **Gray Circle**: Cannot check (system page)
- ⚠️ **Warning Icon**: API connection issue

## Need More Help?

If the extension is still showing "loading loading":

1. Check the browser console (F12) for errors
2. Verify the Flask app is running and accessible
3. Try reloading the extension
4. Check if your antivirus is blocking localhost connections

The extension has been updated with better error handling and fallback mechanisms!
