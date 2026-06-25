# GDPR Re-accept Terms Button Fix

## Issue
The "Re-accept Terms" button on the Account Settings page (GDPR & Legal section) was displaying but not functional. It was trying to use Bootstrap modal syntax (`data-bs-toggle="modal"`) to trigger an Alpine.js controlled modal, which is incompatible.

## Root Cause
- Button was using Bootstrap modal attributes: `data-bs-toggle="modal"` and `data-bs-target="#consentModal"`
- The GDPR consent modal is controlled by Alpine.js (not Bootstrap)
- Alpine.js uses reactive state management with methods like `openModal()`
- Bootstrap modal trigger couldn't access Alpine.js data structures

## Solution Implemented

### 1. Added `openModal()` Method to Alpine.js Modal
**File:** `templates/gdpr/consent_modal.html`

Added a new public method to the `consentModal()` Alpine.js function:
```javascript
openModal() {
  console.log('[GDPR Modal] openModal() called - opening modal');
  this.open = true;
},
```

This allows external scripts to programmatically open the modal.

### 2. Updated Button to Trigger Alpine.js Modal
**File:** `cric/templates/cric/pages/profile_settings.html`

Changed from Bootstrap syntax:
```html
<button type="button" class="mt-3 btn btn-secondary btn-md w-full"
        data-bs-toggle="modal" data-bs-target="#consentModal">
    {% if request.user|has_consent %}Re-accept{% else %}Accept{% endif %} Terms
</button>
```

To Alpine.js trigger:
```html
<button type="button" class="mt-3 btn btn-secondary btn-md w-full"
        onclick="document.querySelectorAll('[x-data]').forEach(el => { if(el.id === 'consentModal' && el.__x) { el.__x.$data.openModal(); } })">
    {% if request.user|has_consent %}Re-accept{% else %}Accept{% endif %} Terms
</button>
```

## How It Works

1. Button click triggers `onclick` handler
2. Handler finds the element with `id="consentModal"` that has Alpine.js data (`x-data`)
3. Accesses Alpine.js instance via `el.__x`
4. Calls the `openModal()` method on the Alpine.js component data
5. Modal state changes from `open: false` to `open: true`
6. Modal becomes visible to the user

## Testing

### User Flow
1. Navigate to Account Settings
2. Scroll to "Legal & Consent" section
3. See "Re-accept Terms" button
4. Click button
5. ✅ GDPR consent modal appears
6. User can review and accept terms again

### Button States
- **If consent complete:** Button shows "Re-accept Terms"
- **If consent incomplete:** Button shows "Accept Terms"

Both states now trigger the modal successfully.

## Commit Details
- **Commit SHA:** `1023939`
- **Commit Message:** "Fix: Make GDPR Re-accept Terms button functional on settings page"
- **Files Modified:** 2
  - `cric/templates/cric/pages/profile_settings.html`
  - `templates/gdpr/consent_modal.html`
- **Lines Added:** 6
- **Branch:** `stage`

## Related Files
- `templates/gdpr/consent_modal.html` - Alpine.js modal component
- `cric/templates/cric/pages/profile_settings.html` - Settings page UI
- `apps/gdpr/context_processors.py` - Consent status logic
- `apps/gdpr/views.py` - Consent acceptance handling

## Deployment Notes
This fix is included in the PR #54 (GDPR Consent System & Temporary Scoring Access) and will be deployed to master when the PR is merged.

## Future Improvements
- Could extract the onclick logic to a separate Alpine.js helper function for cleaner code
- Could add animation feedback to indicate the button was clicked
- Could store button reference in Alpine.js component for more direct access
