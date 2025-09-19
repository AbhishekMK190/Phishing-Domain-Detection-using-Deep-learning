# Phishing Domain Checker Extension (Chrome MV3)

This extension posts the current tab URL to your local Flask API (`/api/check`) and shows a red warning banner when the model flags a page as phishing.

## Prerequisites
- Flask app running at `http://127.0.0.1:5000` (endpoint `/api/check` exists).
- CORS enabled for `/api/*` in `app.py`.

## Install (Chrome)
1. Open Chrome → `chrome://extensions`.
2. Enable Developer mode.
3. Click "Load unpacked" and select this `extension/` folder.
4. Optional: Open the extension options page to change the API base URL.

## Popup UI
- Click the extension icon to open the popup.
- It shows the current tab's status: LEGITIMATE or PHISHING with score.
- You can edit and save the API base URL directly from the popup.

## How it works
- `content.js` runs on every page and sends `{ url: window.location.href }` to `<API_BASE>/api/check`.
- If the response is `{ status: "ok", label: "phishing" }`, a red banner is injected at the top with the score.

## Files
- `manifest.json`: Manifest V3 configuration
- `background.js`: sets a default API base in storage
- `content.js`: calls the API and shows the banner
- `options.html`: change API base URL

## Troubleshooting
- No banner: ensure the Flask app is reachable at `http://127.0.0.1:5000`.
- CORS error: verify `CORS(app, resources={r"/api/*": {"origins": "*"}})` is present in `app.py`.



