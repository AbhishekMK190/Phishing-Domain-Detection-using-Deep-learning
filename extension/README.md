# 🛡️ Quanta AI - Browser Extension

**Advanced real-time phishing protection with AI-powered detection and automatic alerts.**

## ✨ Features

### 🚀 **Automatic Protection**
- **Real-time scanning** of every website you visit
- **Instant popup notifications** with beautiful, modern UI
- **Smart caching** for faster subsequent checks
- **Background monitoring** with minimal performance impact

### 🎨 **Modern Interface**
- **Sleek popup** with gradient backgrounds and smooth animations
- **Visual status indicators** (Safe ✅, Warning ⚠️, Danger 🚨)
- **Risk score display** with detailed information
- **Responsive design** that works on all screen sizes

### ⚙️ **Advanced Settings**
- **Configurable API endpoint** for your PhishGuard server
- **Customizable notifications** (show/hide safe sites)
- **Sound alerts** for threats
- **Cache management** with statistics

## 📦 Installation

### Chrome/Edge Installation:
1. Open your browser and go to `chrome://extensions/` or `edge://extensions/`
2. Enable **"Developer mode"** in the top right
3. Click **"Load unpacked"** and select this `extension` folder
4. The 🛡️ Quanta AI extension will appear in your toolbar

## ⚙️ Configuration

### Initial Setup:
1. **Click the extension icon** 🛡️ in your toolbar
2. **Click "Settings"** in the popup footer
3. **Configure your preferences:**
   - **API Base URL**: `http://127.0.0.1:5000` (default)
   - **Automatic Protection**: Enable/disable auto-checking
   - **Safe Notifications**: Show notifications for safe sites
   - **Sound Alerts**: Enable audio warnings

## 🚀 Usage

### Automatic Mode (Recommended):
- **Just browse normally!** PhishGuard Pro automatically checks every website
- **Notifications appear** in the top-right corner of pages
- **Safe sites** show briefly (4 seconds) then disappear
- **Threats** stay visible until manually closed

## 🎨 Notification Types

### ✅ **Safe Website**
- **Green gradient** background
- **Checkmark icon** ✅
- **Auto-hides** after 4 seconds

### ⚠️ **Suspicious Website**
- **Orange gradient** background
- **Warning icon** ⚠️
- **Stays visible** for 8 seconds

### 🚨 **Phishing Detected**
- **Red gradient** background with pulsing animation
- **Alert icon** 🚨
- **Persistent notification** (doesn't auto-hide)
- **Action buttons** (Report False Positive, Leave Site)

## 🔗 Integration

### PhishGuard API Requirements:
- **POST /api/check** endpoint accepting `{"domain": "example.com"}`
- **GET /api/health** endpoint for status checks
- **JSON responses** with `{"status": "ok", "label": "legitimate", "score": 0.1}`

## 🐛 Troubleshooting

### Common Issues:

**Extension not working:**
- Check if PhishGuard server is running on `http://127.0.0.1:5000`
- Verify API endpoint in extension settings
- Look for errors in browser console (F12)

**No notifications appearing:**
- Ensure "Automatic Protection" is enabled in settings
- Check if you're on a supported page (not chrome:// or file://)
- Verify content script permissions

**API connection failed:**
- Test connection in extension settings
- Check firewall/antivirus blocking local connections
- Verify PhishGuard server is accessible

---

**🛡️ Stay protected with PhishGuard Pro!**



