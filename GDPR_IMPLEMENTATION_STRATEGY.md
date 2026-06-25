# 🇧🇪 GDPR Implementation Strategy for Indcric

## Executive Summary

This document outlines a comprehensive GDPR compliance implementation strategy for the Indcric cricket app, which is Belgium-based with mandatory WhatsApp integration for voting on polls.

**Key Compliance Requirements:**
- ✅ Belgium operates under EU GDPR (strict compliance)
- ✅ WhatsApp phone number is **MANDATORY** (contractual necessity, not consent)
- ✅ Zero data retention (user deletion = complete data erasure)
- ✅ Infrastructure: Django + Neon PostgreSQL (EU-based)
- ✅ Bot integration: WhatsApp voting + group notifications

---

## 1. Current State Analysis

### 1.1 Existing Data Collection

| Data Field | Model | Status | GDPR Implication |
|-----------|-------|--------|------------------|
| `username` | User | Built-in | Personal data - required for auth |
| `email` | User | Built-in | Personal data - required for account |
| `phone` | User | Existing | Personal data - mandatory for WhatsApp |
| `password` | User | Built-in | Auth credential - required |
| `first_name` | User | Built-in | Personal data - optional |
| `last_name` | User | Built-in | Personal data - optional |
| `avatar` | User | Existing | Biometric data - optional |
| `batting_rating` | User | Existing | Derived data - from gameplay |
| `bowling_rating` | User | Existing | Derived data - from gameplay |
| `fielding_rating` | User | Existing | Derived data - from gameplay |
| `vote` (yes/no) | Vote (polls.Vote) | Existing | Behavioral data - tied to user |
| `wa_message_id` | BotEvent | Existing | Bot communication log |
| `bot_events` | BotEvent | Existing | Interaction history |
| `outbound_messages` | OutboundMessage | Existing | Bot message queue/log |

### 1.2 WhatsApp Infrastructure

**Current Implementation:**
- ✅ WhatsApp bot receives/sends messages
- ✅ Vote recording via `BotEvent` model
- ✅ Phone number stored in `User.phone` (unencrypted)
- ✅ Message queue in `OutboundMessage` model
- ✅ Group chat capable (via `target` field in OutboundMessage)

**GDPR Concerns:**
- ⚠️ Phone numbers NOT encrypted at rest
- ⚠️ No consent tracking model
- ⚠️ No data deletion cascade
- ⚠️ No data export functionality
- ⚠️ No privacy policy/terms tracking

---

## 2. GDPR Compliance Architecture

### 2.1 New App: `apps/gdpr/`

Create a dedicated GDPR compliance app to handle:
- Consent tracking
- User data access/export
- User data deletion
- Audit logging
- Privacy preferences

### 2.2 Models to Create

#### A. UserConsent Model
```
Purpose: Track user's acceptance of privacy policy and terms
Location: apps/gdpr/models.py

Fields:
- user (OneToOneField to User)
- privacy_policy_accepted (Boolean)
- privacy_policy_version (CharField) - v1, v2, etc.
- terms_accepted (Boolean)
- terms_version (CharField)
- whatsapp_mandatory_acknowledged (Boolean)
  └─ Message: "I understand WhatsApp is required for voting"
- feature_announcements_accepted (Boolean) [optional]
  └─ Message: "I opt-in to feature announcements"
- group_chat_accepted (Boolean) [optional]
  └─ Message: "I opt-in to group poll discussions"
- accepted_at (DateTimeField)
- updated_at (DateTimeField)
- ip_address (GenericIPAddressField, nullable)
- user_agent (CharField, nullable) - for audit
```

#### B. UserWhatsAppPreference Model
```
Purpose: Manage WhatsApp-specific preferences
Location: apps/gdpr/models.py

Fields:
- user (OneToOneField to User)
- opted_in_polls (Boolean, default=True) - can opt-out
- opted_in_groups (Boolean, default=False) - must opt-in
- opted_in_announcements (Boolean, default=False) - must opt-in
- last_opt_out_at (DateTimeField, nullable)
- opt_out_reason (TextField, blank=True)
- updated_at (DateTimeField, auto_now=True)
```

#### C. DataAccessLog Model
```
Purpose: Audit trail for GDPR data access requests
Location: apps/gdpr/models.py

Fields:
- user (ForeignKey to User)
- action ('download', 'delete', 'export', 'restrict')
- requested_at (DateTimeField, auto_now_add=True)
- completed_at (DateTimeField, nullable)
- status ('pending', 'completed', 'failed')
- notes (TextField, blank=True)
- ip_address (GenericIPAddressField)
```

#### D. ConsentChange Model (optional, for audit trail)
```
Purpose: Track consent modifications over time
Location: apps/gdpr/models.py

Fields:
- user (ForeignKey to User)
- field_name (CharField) - which field changed
- old_value (BooleanField)
- new_value (BooleanField)
- changed_at (DateTimeField, auto_now_add=True)
- reason (CharField, max_length=100, blank=True)
```

### 2.3 Encryption for Phone Numbers

**Implementation Strategy:**
- Use `django-encrypted-model-fields` or `django-fernet` for AES-256 encryption
- Encrypt phone numbers in User model before storing
- Decrypt only when:
  - User views their profile
  - Admin needs to contact user
  - User data export
  - Account deletion confirmation

**Why:** Phone numbers are highly sensitive PII under GDPR

---

## 3. User Flows

### 3.1 New User Signup Flow

```
Step 1: Signup Page
├── Email (required)
├── Password (required)
└── Confirm Password (required)
    └─ Submit

Step 2: WhatsApp Setup (Mandatory)
├── Heading: "WhatsApp Required for Voting"
├── WhatsApp Number (required field)
├── Note: "This is required to participate in poll voting"
└─ Submit
    └─ Send SMS/Bot verification: "Hi [Name]! Reply VERIFY"

Step 3: User Verifies
├── User receives bot message
├── User replies "VERIFY"
└─ Backend marks WhatsApp as verified

Step 4: Policy Acceptance (Mandatory)
├── Show Privacy Policy (scrollable)
├── Show Terms of Service (scrollable)
├── Checkboxes (all required):
│  ├─ ☐ "I have read and accept the Privacy Policy"
│  ├─ ☐ "I accept the Terms of Service"
│  └─ ☐ "I understand WhatsApp is required to vote"
├── Submit
└─ Create UserConsent record with all flags=True

Step 5: Optional Features (Optional)
├── Heading: "Stay Updated (Optional)"
├── Checkboxes:
│  ├─ ☐ "Receive feature announcements via WhatsApp"
│  └─ ☐ "Join group chats for poll discussions"
└─ Save preferences to UserWhatsAppPreference

Step 6: Confirmation Email
├── Send email with:
│  ├─ Consent confirmation
│  ├─ Copy of Privacy Policy
│  ├─ Terms of Service
│  ├─ WhatsApp verification status
│  └─ How to manage preferences
└─ Account fully active
```

### 3.2 Existing User Acceptance Flow

Since users signed up before GDPR implementation:

```
User Logs In
└─ Check: Is UserConsent record present?
   ├─ If YES → Skip to normal flow
   └─ If NO → Show blocking modal

Blocking Modal:
├── Heading: "Important: Privacy Policy Update"
├── Message: "We're committed to GDPR compliance. 
│   Please review and accept our Privacy Policy 
│   and Terms of Service."
├── Buttons:
│  ├─ "View Privacy Policy" (opens in new tab)
│  ├─ "View Terms" (opens in new tab)
│  └─ "I Accept & Continue" (disabled until read)
│
├── After Click "I Accept":
│  ├─ Check: Does user have phone number?
│  │  ├─ If YES (existing) → Skip WhatsApp step
│  │  └─ If NO → Show WhatsApp setup
│  │
│  └─ Show optional preferences
│     ├─ Announcements opt-in
│     └─ Group chat opt-in
│
└─ Create UserConsent record
   └─ Redirect to dashboard
```

---

## 4. User Rights Implementation

### 4.1 Right to Access (Download My Data)

**Location:** Settings → Privacy & Consent → "Download My Data"

**What Gets Exported:**
```json
{
  "personal_data": {
    "username": "user123",
    "email": "user@example.be",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+32491234567",
    "date_joined": "2024-01-15T10:30:00Z"
  },
  "profile_data": {
    "batting_rating": 3.5,
    "bowling_rating": 2.8,
    "fielding_rating": 3.2,
    "matches_played": 12,
    "runs_scored": 450,
    "wickets_taken": 8
  },
  "voting_history": [
    {
      "poll_id": 1,
      "poll_question": "Should we play this session?",
      "vote_choice": "yes",
      "voted_at": "2024-03-20T14:00:00Z",
      "session": "March Session"
    },
    ...
  ],
  "consent_records": [
    {
      "privacy_policy_accepted": true,
      "privacy_policy_version": "v1",
      "terms_accepted": true,
      "terms_version": "v1",
      "whatsapp_mandatory_acknowledged": true,
      "feature_announcements_accepted": false,
      "group_chat_accepted": false,
      "accepted_at": "2024-01-15T11:00:00Z"
    }
  ],
  "whatsapp_preferences": {
    "opted_in_polls": true,
    "opted_in_groups": false,
    "opted_in_announcements": false,
    "updated_at": "2024-03-25T09:00:00Z"
  },
  "bot_interactions": [
    {
      "message_id": "wamid.123456",
      "type": "inbound",
      "action": "vote_received",
      "timestamp": "2024-03-20T14:00:00Z",
      "payload": {"choice": "yes"}
    },
    ...
  ]
}
```

**Format Options:**
- JSON (default)
- CSV (for easy viewing in spreadsheet)

**Process:**
1. User clicks "Download My Data"
2. Backend generates export
3. Email with download link sent to user
4. Link valid for 24 hours
5. Log in DataAccessLog: 'download', 'completed'

### 4.2 Right to Rectification (Edit Profile)

**Already Exists:** User can update:
- First/last name
- Avatar
- Ratings (auto-updated)

**GDPR Addition:**
- Track changes with timestamp
- Optional: send confirmation email when email/phone changes
- Log in DataAccessLog: 'update', 'completed'

### 4.3 Right to Erasure (Delete Account)

**Location:** Settings → Privacy & Consent → "Delete Account Permanently"

**Two-Step Process:**

**Step 1: Request Deletion**
```
Modal:
├── Heading: "Delete Your Account Permanently"
├── Warning: "This action cannot be undone"
├── List what will be deleted:
│  ├─ Profile information
│  ├─ All voting history
│  ├─ All personal data
│  └─ WhatsApp preferences
├── Checkbox: "I understand this is permanent"
└── Button: "Send Confirmation Email"
   └─ Send email: "Confirm account deletion"
      └─ Include secure link valid for 24 hours
```

**Step 2: Confirm via Email**
```
User clicks email link
└─ Confirmation page
   ├── Heading: "Final Confirmation"
   ├── Show: "Account: user123"
   ├── Show: "Email: user@example.be"
   ├── Button: "Yes, Delete Everything"
   └─ On click:
      ├─ Cascade delete all user data:
      │  ├─ Delete User record
      │  ├─ Delete PlayerProfile
      │  ├─ Delete Vote records (cascades)
      │  ├─ Delete BotEvent records (cascades)
      │  ├─ Delete UserConsent records
      │  ├─ Delete UserWhatsAppPreference
      │  ├─ Delete ActivityEvent (where user is actor)
      │  └─ Delete avatar file
      │
      ├─ Remove WhatsApp number from bot:
      │  └─ Send bot: "DELETE_USER:{phone}"
      │
      ├─ Create DataAccessLog: 'delete', 'completed'
      │
      └─ Send email confirmation:
         └─ "Your account has been deleted"
```

**What Gets Deleted:**
- ✅ User account
- ✅ Profile data
- ✅ Voting history
- ✅ Avatar file
- ✅ All personal data
- ✅ All WhatsApp numbers
- ✅ Consent records
- ✅ Bot event logs (linked to user)
- ⚠️ Activity feed (marked as "Deleted User")
- ⚠️ Matches data (kept anonymized for stats)

**What Stays (Anonymized):**
- Match results (no user reference)
- Aggregate statistics (no personal data)
- Backup data (deleted after 30 days)

### 4.4 Right to Restrict Processing

**Location:** Settings → Privacy & Consent → "Manage Preferences"

**Options:**
1. **Suspend Account**
   - Temporarily disable voting
   - Stop WhatsApp messages
   - Keep data (can reactivate later)
   - Can reactivate anytime

2. **Opt-Out of Specific Services**
   - Poll voting: "Stop sending me poll messages"
   - Group chats: "Don't add me to groups"
   - Announcements: "Don't send announcements"
   - Can re-opt-in anytime

### 4.5 Right to Data Portability

**Same as Right to Access** - Download My Data in standard format (JSON/CSV)

---

## 5. Privacy Policy Content (Belgium-Specific)

### Structure:
```
1. INTRODUCTION
   - Who we are (company name, address, Belgium)
   - Contact info, DPO info
   - Privacy policy scope

2. DATA WE COLLECT
   - Table of data types, source, purpose

3. LEGAL BASIS FOR PROCESSING
   - Contractual (WhatsApp mandatory)
   - Consent (opt-in features)
   - Legitimate interest (security)

4. WHATSAPP INTEGRATION
   - Why phone is mandatory
   - What we do with WhatsApp number
   - Encryption & security
   - Bot message types
   - Opt-out options

5. VOTING & POLLS
   - How votes are recorded
   - Vote privacy (who can see)
   - Data retention (until deletion)
   - Vote anonymization

6. DATA RETENTION
   - Policy: "All data deleted when account deleted"
   - Backups: "Kept 30 days, then deleted"
   - WhatsApp logs: "As per bot provider policy"

7. YOUR RIGHTS
   - Download data
   - Delete account
   - Update information
   - Restrict processing
   - Lodge complaint (APD link)

8. SECURITY
   - Encryption (AES-256 for phone)
   - HTTPS only
   - EU data storage (Neon, Belgium region)
   - No third-party sharing

9. THIRD PARTIES
   - Neon (database provider)
   - WhatsApp (messaging)
   - Cloudinary (avatars, optional)
   - Analytics (none currently)

10. CHILDREN
    - Not directed at children under 13
    - Parental consent required if under 18

11. POLICY CHANGES
    - How we notify users
    - Your right to re-accept

12. CONTACT & COMPLAINTS
    - Email for questions
    - APD Belgium contact: apd.belgium.be
```

---

## 6. Terms of Service Addition

**Section: WhatsApp Requirement**

```
3. MANDATORY WHATSAPP

3.1 WhatsApp Account Required
- WhatsApp phone number is MANDATORY to use this service
- You must be reachable via WhatsApp
- You authorize us to use your number for voting communications

3.2 What We Do With Your WhatsApp Number
- Send poll voting requests (1-3 per week typically)
- Verify your account via bot message
- Send match updates and notifications
- Record your votes

3.3 Your Obligations
- Provide a valid, working WhatsApp number
- Keep your phone number current
- Reply to verification messages
- Don't share your account credentials

3.4 Opt-Out and Withdrawal
- Reply "STOP" to any bot message to opt-out of polls
- Manage preferences in Settings
- Still must keep WhatsApp active for feature access
- Can delete account anytime to remove all data

3.5 Data Processing
- Your phone number is encrypted
- Your votes are tied to your account
- Votes can be aggregated but not shared individually
- All data deleted when you delete your account

3.6 Non-Compliance
- If you don't provide/maintain valid WhatsApp:
  - Cannot participate in voting
  - May lose access to features
  - Can restore by re-adding phone number
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Set up models and infrastructure

- [ ] Create `apps/gdpr/` app
- [ ] Create models:
  - [ ] `UserConsent`
  - [ ] `UserWhatsAppPreference`
  - [ ] `DataAccessLog`
  - [ ] `ConsentChange`
- [ ] Create database migrations
- [ ] Install encryption library (`django-fernet`)
- [ ] Update `User.phone` with encryption
- [ ] Create admin interface for GDPR models

**Deliverable:** Models in place, admin access

### Phase 2: Signup & Onboarding (Week 1-2)
**Goal:** Implement consent during signup

- [ ] Create signup form with WhatsApp field
- [ ] Add WhatsApp verification flow (bot message)
- [ ] Create privacy policy acceptance form
- [ ] Create terms acceptance form
- [ ] Add optional preferences form
- [ ] Send confirmation email
- [ ] Create UserConsent on signup

**Deliverable:** New users collect consent properly

### Phase 3: Existing User Migration (Week 2)
**Goal:** Get existing users to accept policies

- [ ] Create consent modal for login
- [ ] Add WhatsApp setup for existing users
- [ ] Create migration for existing users
- [ ] Send email reminder (Day 1, 7, 30)
- [ ] Show banner if not accepted

**Deliverable:** Existing users prompted for consent

### Phase 4: Data Access Rights (Week 2-3)
**Goal:** Implement "Download My Data"

- [ ] Create data export service
- [ ] Create export view (JSON/CSV)
- [ ] Add "Download My Data" button to Settings
- [ ] Create email delivery flow
- [ ] Log in DataAccessLog
- [ ] Add download link expiration (24h)

**Deliverable:** Users can export their data

### Phase 5: Data Deletion (Week 3)
**Goal:** Implement full account deletion

- [ ] Create deletion request form
- [ ] Add email verification step
- [ ] Create cascading deletion logic
- [ ] Add bot notification (unsubscribe)
- [ ] Create deletion confirmation email
- [ ] Log in DataAccessLog

**Deliverable:** Users can fully delete accounts

### Phase 6: Preferences Management (Week 3)
**Goal:** Implement optional preferences

- [ ] Create WhatsApp preferences form
- [ ] Add opt-in/opt-out toggles
- [ ] Create bot opt-out handler ("STOP")
- [ ] Log preference changes
- [ ] Send confirmation emails

**Deliverable:** Users can manage WhatsApp preferences

### Phase 7: Documentation & Legal (Week 4)
**Goal:** Create legal documents

- [ ] Draft Privacy Policy
- [ ] Draft Terms of Service updates
- [ ] Create Data Retention Policy
- [ ] Create Data Breach Response Plan
- [ ] Review with legal counsel
- [ ] Deploy to website

**Deliverable:** Legal documents finalized

### Phase 8: Testing & QA (Week 4)
**Goal:** Comprehensive testing

- [ ] Test signup flow (new users)
- [ ] Test existing user migration
- [ ] Test data export completeness
- [ ] Test account deletion cascade
- [ ] Test bot integration
- [ ] Test email delivery
- [ ] Security audit

**Deliverable:** All flows tested, production-ready

---

## 8. Security Considerations

### 8.1 Data Encryption

| Data Type | Encryption | Location |
|-----------|-----------|----------|
| Phone Numbers | AES-256 (Fernet) | User.phone |
| Passwords | Django bcrypt | User.password |
| Backups | Encrypted at rest | Neon backups |
| Exports | HTTPS only | Email delivery |

### 8.2 Access Control

- Only user can request their data
- Only user can delete their account
- Admin dashboard for support staff (limited access)
- IP logging for audit trail
- User agent logging for device tracking

### 8.3 Data Retention

```
Type              | Retention       | After Deletion
------------------|-----------------|------------------
User Data         | Until deletion  | 0 days (instant)
Consent Records   | Until deletion  | 0 days (instant)
Bot Events        | 90 days         | Purged after 90 days
Backups           | 30 days         | Deleted after 30 days
Logs              | 90 days         | Purged after 90 days
Email Logs        | 30 days         | Purged after 30 days
```

### 8.4 Compliance Audit

**Annual:**
- [ ] Data breach assessment
- [ ] Third-party DPA review (Neon, WhatsApp)
- [ ] Data retention audit
- [ ] Encryption key rotation
- [ ] Privacy policy update

**Quarterly:**
- [ ] Consent metrics review
- [ ] Deletion requests audit
- [ ] Data access requests audit
- [ ] Security patch review

---

## 9. Bot Integration Points

### 9.1 Verification Message (New User)

```
Bot sends to new phone number:

"Hi [First Name]! 👋

Welcome to Indcric. We need to verify your WhatsApp 
to complete your account setup.

Reply: VERIFY

---
Privacy: [link to policy]
STOP to unsubscribe"
```

### 9.2 Poll Notification

```
"🏏 NEW POLL: Should we play this session?

Match: [Session Name]
Date: [Date]

Vote now:
👍 Reply YES
👎 Reply NO

Your vote helps us organize better matches!

---
STOP to pause polls
Privacy: [link]"
```

### 9.3 Opt-Out Handler

```
Bot receives: "STOP" or "UNSUBSCRIBE"

Action:
├─ Mark user as opted_out (WhatsAppPreference)
├─ Set opted_in_polls = False
├─ Log in BotEvent
├─ Send confirmation:
   "✋ You've been unsubscribed from poll messages.
    
    You can re-enable in Settings at [link]
    
    Reply YES to resubscribe"
└─ Notify backend via webhook
```

### 9.4 Group Invitation (Future)

```
"🏏 Join our cricket group!

We discuss upcoming matches and vote on polls 
using emoji reactions.

Only members can see messages. You can leave anytime.

Reply: YES to join
or STOP to skip

---
Privacy: [link]"
```

---

## 10. Monitoring & Compliance

### 10.1 Metrics to Track

```
Weekly:
- New users created
- Users who completed consent
- Users who provided WhatsApp
- Users who verified WhatsApp
- Data export requests
- Account deletion requests

Monthly:
- Consent acceptance rate
- WhatsApp verification success rate
- Opt-out rate (polls)
- Data breach attempts (zero)
- Support requests (privacy-related)

Quarterly:
- DPA compliance checklist
- Neon security review
- Encryption key audit
- Data retention review
```

### 10.2 Belgium APD (Data Authority)

**Contact for Complaints:**
- Email: contact@apd-gba.be
- Website: apd.belgium.be
- Address: Autorité de la Protection des Données (Belgium)

**Requirements:**
- Response to data requests within 30 days
- Breach notification within 72 hours
- Privacy impact assessment (if large-scale)
- DPA contact info in Privacy Policy

---

## 11. Implementation Checklist

### Models & Database
- [ ] Create `apps/gdpr/models.py` with all models
- [ ] Create migrations
- [ ] Run migrations
- [ ] Create admin interface
- [ ] Test model relationships

### Encryption
- [ ] Install `django-fernet`
- [ ] Create encryption settings
- [ ] Update `User.phone` field
- [ ] Create migration for existing data
- [ ] Test encrypt/decrypt

### Forms & Views
- [ ] Signup form with WhatsApp
- [ ] WhatsApp verification view
- [ ] Consent acceptance form
- [ ] Preferences form
- [ ] Settings page (GDPR section)

### Data Access Rights
- [ ] Download My Data view
- [ ] JSON export generator
- [ ] CSV export generator
- [ ] Email delivery
- [ ] Link expiration

### Data Deletion
- [ ] Delete request form
- [ ] Email verification
- [ ] Cascading delete logic
- [ ] Bot unsubscribe notification
- [ ] Confirmation email

### Legal Documents
- [ ] Privacy Policy
- [ ] Terms of Service
- [ ] Data Retention Policy
- [ ] Breach Response Plan

### Testing
- [ ] Full signup flow
- [ ] Existing user migration
- [ ] Data export
- [ ] Account deletion
- [ ] Bot integration
- [ ] Security audit

---

## 12. Success Criteria

✅ **Implementation Success When:**
1. All new users go through consent flow
2. All existing users have consent record
3. Users can export their complete data
4. Users can delete accounts with full cascade
5. WhatsApp preferences enforced
6. No unencrypted personal data in logs
7. All GDPR rights implemented
8. Legal documents published
9. Zero data breaches
10. Audit trail complete

---

## 13. Next Steps

**Immediate (This Week):**
1. ✅ Review and approve this strategy
2. ⬜ Create the gdpr app and models
3. ⬜ Set up encryption
4. ⬜ Start Phase 1 implementation

**This Month:**
1. ⬜ Complete signup flow
2. ⬜ Migrate existing users
3. ⬜ Implement data access rights
4. ⬜ Draft legal documents

**This Quarter:**
1. ⬜ Full testing and QA
2. ⬜ Legal review
3. ⬜ Security audit
4. ⬜ Production deployment

---

## References

- [GDPR Official Text](https://gdpr-info.eu/)
- [Belgian Data Authority](https://apd.belgium.be/)
- [GDPR for Developers](https://www.gdpr.eu/)
- [Django Security](https://docs.djangoproject.com/en/5.1/topics/security/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/business-platform/get-started)

---

**Document Version:** 1.0  
**Created:** June 24, 2026  
**Status:** Ready for Implementation  
**Next Review:** After Phase 1 Completion
