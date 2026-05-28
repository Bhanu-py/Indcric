# WhatsApp Guest Votes — Accept RSVPs from Unregistered Numbers

**Status:** Planning. No code yet.
**Owner:** Bhanu
**Created:** 2026-05-28
**Related:** [whatsapp-bot.md](whatsapp-bot.md), [whatsapp-bot-HANDOVER.md](whatsapp-bot-HANDOVER.md)

## Goal

When a WhatsApp user RSVPs to a session poll via the bot but their phone number isn't in `User.phone`, record the vote anyway — keyed on their WhatsApp number and display name — and surface them in the app's poll UI alongside registered voters. Today those messages get rejected with "I don't recognise this number" and the vote is lost.

## Why this matters

- The group-share flow ([whatsapp-bot.md](whatsapp-bot.md) "Cost Pivot") brings in casuals and guests who tap the `wa.me` deep link from the group. They expect their vote to count — getting told "register first" is friction at the wrong moment.
- Captains/admins want to see a single combined count of "who's coming," not "registered yes" + a separate guess for guests.
- We can capture the guest's WhatsApp display name from the webhook payload (`value.contacts[0].profile.name`), so guests get shown as a real name, not just a phone number.

## Hard constraint (recap)

Meta's WhatsApp Cloud API **cannot read group messages or native group polls**. This feature does NOT pull votes from a native WhatsApp poll in the group — only from DMs sent to the bot. The group-share path is unchanged: members tap the `wa.me` link in the group, which opens a DM to the bot with `YES <session_id>` pre-filled. That DM is the only signal we receive. If we ever want to read native group polls, that requires switching to a `whatsapp-web.js` group-member bot ([whatsapp-bot-HANDOVER.md](whatsapp-bot-HANDOVER.md)) — out of scope here.

## Scope

### In scope
- Record guest votes from unregistered phones via the existing `whatsapp_webhook` flow.
- Capture and store the WhatsApp **profile name** the sender's account broadcasts (`contacts[0].profile.name`).
- Show guest voters in:
  - `session_detail` page (the YES/NO voter chip rows in [session_detail.html](../../cric/templates/cric/pages/session_detail.html))
  - `poll_detail` page (vote counts and lists)
  - STATUS reply (`_handle_status` in [apps/notifications/views.py](../../apps/notifications/views.py))
- Idempotent re-vote: same WA number flipping YES↔NO updates the existing guest Vote row, doesn't create a duplicate.
- Admin-side "claim" path: when a guest later registers and adds their phone to their `User` profile, their historical guest Votes should be reattributed to the new user. See "Claim flow" below.

### Out of scope (deferred)
- Reading native WhatsApp polls in a group. (Cloud API can't.)
- Counting guests in `cost_per_person` — keep cost split among registered/paying members for now, otherwise we'll be invoicing wallets we don't have.
- Auto-creating a `User` row for the guest. We want explicit registration so we don't pollute the user table with one-shot taps.
- Letting guests use `BALANCE` / `STATUS` (they have no wallet; `STATUS` is debatable — see Open Questions).

## Schema changes

### `apps/polls/models.py` — `Vote`

```python
class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True, blank=True,           # ← was required
    )
    # Guest fields — populated when user is None
    wa_phone = models.CharField(max_length=20, blank=True, default='')
    wa_name = models.CharField(max_length=100, blank=True, default='')

    CHOICES = (('yes', 'Yes'), ('no', 'No'))
    choice = models.CharField(max_length=3, choices=CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['poll', 'user'],
                condition=models.Q(user__isnull=False),
                name='vote_unique_poll_user',
            ),
            models.UniqueConstraint(
                fields=['poll', 'wa_phone'],
                condition=models.Q(user__isnull=True),
                name='vote_unique_poll_wa_phone',
            ),
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | ~models.Q(wa_phone=''),
                name='vote_user_or_wa_phone_required',
            ),
        ]
```

Notes:
- Drop the existing `unique_together = ('poll', 'user')` — Django's `UniqueConstraint` with a condition is the equivalent that tolerates `NULL` user.
- `wa_phone` stores the same normalised E.164 string already used in [apps/notifications/views.py](../../apps/notifications/views.py) `_normalize_inbound_phone` — `+`-prefixed, digits only. The `_normalize_inbound_phone` helper is reused; no new normalisation logic.
- `wa_name` is `max_length=100` to match WhatsApp's profile-name cap.
- `blank=True, default=''` (not `null=True`) on the string fields — standard Django convention for optional CharFields. Keeps queries simple (`wa_phone=''` means "no guest number").

### Migration

Single migration `apps/polls/migrations/0002_vote_guest.py`:
1. `AlterField` to make `user` nullable.
2. Add `wa_phone`, `wa_name`.
3. `AlterUniqueTogether` to remove the old `(poll, user)` unique.
4. `AddConstraint` × 3 for the two partial-unique + check above.

Reversible. Backfill not required — every existing Vote has a non-null user, so the new check passes for all existing rows.

## Webhook flow changes ([apps/notifications/views.py](../../apps/notifications/views.py))

### `_handle_rsvp` — current behaviour

```python
user = User.objects.filter(phone=phone).first()
if user is None:
    send_text_message(phone, "I don't recognise this number...")
    return                              # ← drops the vote
...
Vote.objects.update_or_create(poll=poll_obj, user=user, defaults={'choice': choice})
```

### `_handle_rsvp` — new behaviour

1. Always look up `user = User.objects.filter(phone=phone).first()`.
2. Extract guest name from webhook payload — already passed in as `value` to `_process_message`, but `_handle_rsvp` doesn't currently see `value`. Plumb the sender's profile name through:
   - `_process_message` already iterates `value.get('messages', [])`. Read `value.get('contacts', [])[0].get('profile', {}).get('name', '')` once per webhook invocation and pass it to `_process_message` (or extract per message — the contacts array is parallel to messages).
   - Pass `wa_name` into `_handle_rsvp(... wa_name=wa_name)`.
3. Pick the target poll using the existing `session_id`-or-latest-open logic (no change).
4. **Branch on user existence:**
   - `if user is not None`: existing path — `Vote.objects.update_or_create(poll=poll, user=user, defaults={'choice': choice})`.
   - `if user is None`: new path — `Vote.objects.update_or_create(poll=poll, user=None, wa_phone=phone, defaults={'choice': choice, 'wa_name': wa_name})`.
5. Confirmation reply unchanged in shape; greet by `wa_name` if it's a guest so they see we got their name right (e.g. `Got it, Rohan — recorded YES for ...`).
6. Drop the "I don't recognise this number" reply for the RSVP path. Keep it for `BALANCE` (guests have no wallet) — see `_handle_balance`, no change there.

### `_handle_status` — include guests

Current code only lists registered voters. New code:

```python
yes_voters = list(poll.votes.filter(choice='yes').select_related('user'))
no_voters  = list(poll.votes.filter(choice='no').select_related('user'))

def _name(v):
    if v.user_id is not None:
        return _display_name(v.user)
    return v.wa_name or _mask_phone(v.wa_phone)
```

`_mask_phone('+32471123456')` → `+32 47•••3456` — preserves country + last 4, hides the middle. We don't want STATUS replies to leak full numbers into the group via screenshots.

## UI surface changes

### `apps/sessions/views.py` (session_detail)

Lines 261-263 currently build:
```python
yes_voters = [{'user': v.user, 'team_assigned': False, 'rating': _combined_rating(v.user)}
              for v in poll.votes.filter(choice='yes').select_related('user')]
no_voters  = [v.user for v in poll.votes.filter(choice='no').select_related('user')]
```

Change to emit voter dicts that handle both registered and guest:

```python
def _voter_dict(v):
    if v.user_id is not None:
        return {
            'kind': 'user',
            'user': v.user,
            'display_name': v.user.first_name or v.user.username,
            'rating': _combined_rating(v.user),
            'team_assigned': False,
        }
    return {
        'kind': 'guest',
        'user': None,
        'display_name': v.wa_name or _mask_phone(v.wa_phone),
        'wa_phone': v.wa_phone,
        'rating': None,
        'team_assigned': False,
    }
```

Team-balancing code already checks `voter['user'].id in assigned_ids` (line 289-290) — guard with `if voter['kind'] == 'user'` so guests are skipped (they can't be assigned to a team since they have no `User` row).

### `cric/templates/cric/pages/session_detail.html`

Render guests with a visual distinguisher — small "guest" pill next to the name, and no rating bubble. They appear in the YES/NO lists but cannot be tapped for team assignment.

### `cric/templates/cric/pages/poll_detail.html`

Count includes guests; list shows them with the same "guest" pill treatment.

## Claim flow (later, but plan the seam now)

When a guest later registers and saves a phone number on their User profile, their historical votes should fold into their account.

**Trigger:** in `apps/accounts/forms.py` `ProfileForm.save()` (or wherever `User.phone` is written), after the User is saved with a non-empty phone:

```python
from apps.polls.models import Vote
Vote.objects.filter(user__isnull=True, wa_phone=user.phone).update(
    user=user, wa_phone='', wa_name=''
)
```

Edge case: if the user already has a vote for the same poll, we'd violate the registered-unique constraint. Resolve by:
1. Delete the guest vote where (user, poll) collision exists — prefer the registered vote.
2. Re-attribute everything else.

This is a small follow-up after the main feature lands. Not blocking.

## Implementation order

1. **Schema + migration** — `apps/polls/models.py`, `makemigrations polls`, `migrate`. Verify reverse migration works on a copy of dev DB.
2. **Webhook plumbing** — thread `wa_name` from `_handle_whatsapp_message` → `_process_message` → `_handle_rsvp`. Update `_handle_rsvp` branch logic.
3. **STATUS reply** — update `_handle_status` to include guest voters, with phone masking.
4. **session_detail view + template** — update `_voter_dict` shape, guest pill in template, guard team-assignment code.
5. **poll_detail view + template** — same shape, same pill.
6. **Manual test on dev** — send a YES from an unregistered number via wa.me link, confirm vote appears in UI and STATUS.
7. **Claim flow** — add the reattribute on profile-save (small follow-up PR).

Each step is its own commit. Step 1 must land before any of 2-6.

## Open questions

1. **Guest STATUS access:** if an unregistered phone texts `STATUS`, do we reply with the poll counts, or "register first"? Argument for replying: the guest just voted, they want to see they're on the list. Argument against: leaks roster info to anyone with the bot number. **Recommendation:** reply with counts only (no names) for unregistered senders.
2. **Display fallback when `wa_name` is empty:** WhatsApp profile name can be empty / hidden by privacy settings. We fall back to `_mask_phone(wa_phone)`. Acceptable?
3. **Admin claim trigger:** auto-claim on phone save (proposed above), or surface a "claim X guest votes for this phone" button to admins on a "Pending Guests" page? Auto-claim is simpler and the right default; the admin page is overkill for current volume.
4. **Backfill of existing rejected RSVPs:** `BotEvent` table has `action='rsvp'` rows from unknown phones already (logged via `_log_inbound` before the early-return). Should we backfill these into Vote rows when the feature ships? **Recommendation:** no — they're stale, the polls may be closed, just start fresh.
5. **wa_name max length 100:** WhatsApp docs aren't explicit; 100 is a guess. Confirm by checking a few real payloads in `BotEvent.payload` before migrating.

## What stays the same

- The `wa.me` group-share flow (admin pastes invite into group, members tap link). Untouched.
- `BALANCE` / wallet path. Guests still get the "register first" reply on BALANCE — no wallet exists for them.
- `notify_poll_created`, `resend_poll_invite`, reminder sends. Untouched.
- The `BotEvent` audit trail. The new guest Vote rows are accompanied by `BotEvent(action='rsvp', user=None, phone=..., payload={...})` exactly as today.

## Risk / rollback

- Schema change is additive (new fields, looser constraint on existing field). Rolling back means migrate-zero on polls' new migration — guest votes lost, registered votes preserved (since the `user` column reverts to NOT NULL via `AlterField`; reverse migration must include `user__isnull=False` filter delete for guest rows first, or `migrate` will fail).
- Spam vector: anyone with the bot number can now create a Vote row by texting YES. Mitigation: rate-limit by `wa_phone` per poll (already idempotent via `update_or_create`, so they can flip but not flood). If abuse appears, add a per-`wa_phone`-per-day cap.
- Privacy: guest phone is stored in plaintext in `Vote.wa_phone`. Same exposure as `User.phone` — acceptable, but masked in any UI surface and never printed back into the group via STATUS.
