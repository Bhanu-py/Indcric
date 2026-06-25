# GDPR Consent Modal Testing Checklist

## Prerequisites
✅ Django server is running (fresh restart with all latest code)
✅ User consent has been reset to incomplete
✅ Logging is configured and will show [CONSENT] messages

## Step-by-Step Testing:

### Step 1: Clear Browser Cache
- [ ] Press **Ctrl+Shift+R** (hard refresh) to clear all caches
- [ ] Wait for page to fully load
- [ ] Check browser console for any JavaScript errors

### Step 2: Log Out Completely  
- [ ] Log out from current session (logout completely)
- [ ] Clear cookies if needed
- [ ] Close browser tab and reopen

### Step 3: Log In Again
- [ ] Navigate to http://indcric-ido2.onrender.com/dashboard/
- [ ] Log in with testuser123 credentials
- [ ] **GDPR modal MUST appear** on dashboard

### Step 4: Check Console Logs
- [ ] Open browser Developer Console (F12)
- [ ] Look for console output showing:
  - `[GDPR Modal] data-show-modal attribute value: true`
  - `[GDPR Modal] shouldShow: true`
  - `[GDPR Modal] ✓ Modal OPEN`

### Step 5: Accept Consent
- [ ] **Check Privacy Policy** checkbox ✓
- [ ] **Check Terms of Service** checkbox ✓
- [ ] **Leave WhatsApp UNCHECKED** (it's optional) ☐
- [ ] Click **"Accept & Continue"** button
- [ ] Look in browser console for:
  - "Success" response from server
  - No JavaScript errors

### Step 6: Check Server Logs
- [ ] In the terminal running Django, look for [CONSENT] logs:
  - `[CONSENT] Received POST data:...`
  - `[CONSENT] User: testuser123`
  - `[CONSENT] Checkbox values: privacy=True, terms=True, whatsapp=False`
  - `[CONSENT] Successfully saved consent...`

### Step 7: Verify Modal Closes
- [ ] Modal should close automatically
- [ ] Page should redirect to dashboard
- [ ] **Modal should NOT appear again**

### Step 8: Verify Persistence
- [ ] Refresh the page (F5 normal refresh)
- [ ] **Modal should NOT appear**
- [ ] Navigate away and back
- [ ] **Modal should still NOT appear**

### Expected Success Criteria
✅ Modal appears on first login
✅ User can submit form without WhatsApp checkbox
✅ Database is updated with consent values
✅ Modal closes after successful submission
✅ Modal does NOT show again on subsequent page loads
✅ Server logs show successful consent save

## If Something Fails:
1. Check Django server console for [CONSENT] error messages
2. Check browser developer console (F12) for JavaScript errors
3. Check that all code changes were deployed correctly
4. Verify user consent in database is actually being updated
