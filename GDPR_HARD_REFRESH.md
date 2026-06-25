# GDPR Modal - Hard Refresh Instructions

## Problem
The browser cache was showing old data. The database has been reset, but the page needs a hard refresh.

## Solution
Follow these steps:

### 1. Open the Login Page
Go to: http://localhost:8000/accounts/login/

### 2. HARD REFRESH (clear cache)
- **Windows/Linux**: Press `Ctrl + Shift + R`
- **Mac**: Press `Cmd + Shift + R`

This will:
- Clear the browser cache for this page
- Force a fresh download of all assets
- Load the latest HTML/CSS/JavaScript

### 3. Login with your existing user
Use your credentials to log in

### 4. After Login
You should see the modal appear immediately with:
- "Legal Consent Required" header
- 3 checkboxes:
  - Privacy Policy (required)
  - Terms of Service (required)
  - WhatsApp for Voting (optional)

### 5. Check Browser Console (F12)
The console should show:
```
[GDPR Modal] Initializing...
[GDPR Modal] data-show-modal: true
[GDPR Modal] Modal OPEN (because showConsent=true)
[GDPR Modal] Running $nextTick, current open state: true
```

### 6. Accept Consents
- Check Privacy Policy ✓
- Check Terms of Service ✓
- Click "Accept & Continue"
- You'll be redirected to /dashboard/

---

## If Modal Still Doesn't Show

1. Check the browser console logs (F12 → Console)
2. Look for any JavaScript errors in red
3. Check the Network tab to see the API response
4. Share a screenshot of the console output
