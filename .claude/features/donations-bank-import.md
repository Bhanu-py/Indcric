# Donations — Auto-import from Club Bank Account

**Status:** Planning. No code yet.
**Owner:** Bhanu
**Created:** 2026-06-12
**Related:** [apps/donations/models.py](../../apps/donations/models.py), [apps/donations/views.py](../../apps/donations/views.py), commit 741c1c4 ("Add 'Support the club' donations page")

## Goal

Pull transaction history from the club's bank account (N26), filter incoming credits whose payment reference contains "ICG", and auto-create `Donation` rows so they appear on the support page's contributor wall and campaign-progress bar — without a treasurer manually re-typing every SEPA transfer.

Today: members SEPA-transfer to the N26 IBAN with reference "ICG donation + name"; a treasurer reads the N26 app, then manually logs each one through the form in [log_donation_view](../../apps/donations/views.py#L34). It works, but lags, and small donations get skipped.

## Approach options

N26 has no first-party REST API for retail accounts. Three realistic ways to get the data in:

| Option | Effort | Cost | Automation | Risk |
|---|---|---|---|---|
| **A. GoCardless Bank Account Data (Nordigen)** | Medium | Free for EU PSD2 | Fully automatic, cron-pull every N hours | 90-day SCA re-consent (admin redirect) |
| **B. CSV / CAMT.053 upload** | Low | Free | Admin uploads file manually (weekly?) | Still requires a human pull from N26 |
| **C. Paid aggregator (Plaid / Tink / Salt Edge / Powens)** | Medium | €20–100/mo | Fully automatic | Cost not justifiable for club volume |

**Recommendation: Option A (GoCardless Bank Account Data, formerly Nordigen).**
- Free for EU PSD2-licensed banks. N26 GmbH is in their supported list for BE/DE/FR/ES/IT/NL/AT.
- Official AISP route — no API reverse-engineering, no TOS grey zone.
- Returns transactions with structured remittance fields (`remittanceInformationUnstructured`, `additionalInformation`) — that's where "ICG donation - John" appears.
- Refresh cadence: 4× per day per account is included free.
- One real downside: PSD2 SCA requires re-consent every 90 days (Belgium-specific regulatory rule). Admin must click a link to re-authorize quarterly — surfaced as a banner + email when the requisition is < 14 days from expiry.

Option B is the simple fallback if GoCardless onboarding hits a snag — the parsing/matching logic is the same code path, just fed from a file instead of an API.

## Hard constraints

- **Reference text is the only signal we can rely on.** Counterparty IBAN doesn't appear on every transfer (some banks redact it for non-SEPA), and counterparty name varies by how the donor's bank fills it in. The "ICG" prefix in the reference is what makes a transaction a donation candidate — anything without "ICG" gets ignored.
- **The N26 account also receives non-donation income** (the club's own session-fee collections, transfers between treasurers, etc.). Filtering on reference is critical — never auto-create a Donation just because money came in.
- **Refunds, outgoing payments, and SDD reversals are out of scope** — only positive-amount credit transactions with "ICG" in the reference are candidates.
- **GDPR.** Counterparty IBAN and name are personal data. We already store IBAN on the receiving side ([DonationSettings.iban](../../apps/donations/models.py#L17)); donor IBAN/name will sit in a new `BankTransaction` table. Retention: keep indefinitely for accounting reconciliation, redact on member request.
- **Idempotency.** Every imported transaction has a stable `transactionId` from GoCardless — unique constraint on it prevents double-imports across retries / re-runs.

## Schema changes

New app: **`apps.banking`** (separate from `donations` because the bank link belongs in its own namespace — future use cases: import session-payment confirmations, expense receipts).

### `BankLink`

One row per linked external account. Most clubs will have exactly one; the schema supports more.

```python
class BankLink(models.Model):
    label = models.CharField(max_length=80, help_text="Display name, e.g. 'Club N26'")
    institution_id = models.CharField(max_length=80)        # GoCardless ID e.g. 'N26_NTSBDEB1'
    iban = models.CharField(max_length=34, blank=True)
    requisition_id = models.CharField(max_length=64)        # GoCardless requisition
    account_id = models.CharField(max_length=64)            # GoCardless internal account ID
    consent_valid_until = models.DateTimeField()            # PSD2 90-day SCA limit
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### `BankTransaction`

One row per fetched transaction. Audit trail — never edited after insert.

```python
class BankTransaction(models.Model):
    STATUS_NEW = 'new'
    STATUS_MATCHED = 'matched'       # auto-converted to a Donation
    STATUS_IGNORED = 'ignored'       # admin marked as not-a-donation
    STATUS_REVIEW = 'review'         # has 'ICG' but admin must confirm (config-driven)
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_MATCHED, 'Matched'),
        (STATUS_IGNORED, 'Ignored'),
        (STATUS_REVIEW, 'Needs review'),
    ]

    link = models.ForeignKey(BankLink, on_delete=models.PROTECT, related_name='transactions')
    transaction_id = models.CharField(max_length=128, unique=True)  # GoCardless field
    booked_on = models.DateField()
    value_on = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)   # signed
    currency = models.CharField(max_length=3, default='EUR')
    counterparty_name = models.CharField(max_length=140, blank=True)
    counterparty_iban = models.CharField(max_length=34, blank=True)
    remittance = models.TextField(blank=True)
    raw = models.JSONField(default=dict)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW)
    donation = models.OneToOneField(
        'donations.Donation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bank_transaction',
    )
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-booked_on', '-id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['link', 'booked_on']),
        ]
```

### `Donation` change

Mark donations that came in via auto-import so the UI can show a small badge ("Auto-imported from bank") and so the treasurer can distinguish hand-logged from machine-logged.

```python
class Donation(models.Model):
    ...
    source = models.CharField(
        max_length=10,
        choices=[('manual', 'Manual'), ('bank', 'Bank import')],
        default='manual',
    )
```

The existing reverse `donation.bank_transaction` relation is enough to dig into the source row — `source` is just a denormalised flag for cheap filtering.

## GoCardless integration

Library: **no official SDK for Python**, but the REST API is small. Wrap it ourselves in `apps/banking/services/gocardless.py` — about 6 functions: `_token()`, `list_institutions()`, `create_requisition()`, `get_requisition()`, `get_account()`, `get_transactions(account_id, date_from)`.

Auth: secret_id + secret_key from `https://bankaccountdata.gocardless.com/user-secrets/`. Both go in `.env` (`GOCARDLESS_SECRET_ID`, `GOCARDLESS_SECRET_KEY`). Bearer token is short-lived (24h access + 30d refresh) — cache in Redis or just refetch per cron tick (4×/day = trivial).

### Linking flow (one-time per 90 days)

1. Staff visits `/banking/link/` (staff_member_required).
2. View calls `create_requisition(institution_id='N26_NTSBDEB1', redirect=APP_URL + '/banking/link/callback/', reference=<random>)`.
3. Returns a `link` URL → redirect admin's browser to it → N26 SCA → bounces back to callback.
4. Callback fetches the requisition, reads `accounts[0]`, creates/updates the `BankLink` row with the account ID + `consent_valid_until = now() + 90 days`.
5. Render a "Linked ✅" page with the IBAN it just authorized.

### Polling flow (cron)

Management command `python manage.py import_bank_transactions` (idempotent), called by cron-job.org every 6 hours (same scheduler that runs `run_reminders_view`). Each tick:

1. For each active `BankLink`:
   - If `consent_valid_until < now() + 14 days` → log a warning, send a single admin DM/email per refresh window asking them to re-link.
   - `date_from = link.last_synced_at - 3 days` (overlap window for late-bookings; idempotency dedupes).
   - `txns = gocardless.get_transactions(link.account_id, date_from)`.
2. For each `txn` in `txns['booked']`:
   - `transaction_id` already in DB → skip.
   - Parse fields → build `BankTransaction(status=STATUS_NEW)`.
   - Decide status via `_classify(txn)` (below).
3. Update `link.last_synced_at = now()`.

### `_classify(txn)` — the "ICG filter"

```python
ICG_PATTERN = re.compile(r'\bicg\b', re.IGNORECASE)

def _classify(amount, remittance):
    if amount <= 0:
        return BankTransaction.STATUS_IGNORED
    if not ICG_PATTERN.search(remittance or ''):
        return BankTransaction.STATUS_IGNORED
    # Has 'ICG' AND positive amount → candidate donation.
    return BankTransaction.STATUS_MATCHED   # or STATUS_REVIEW if AUTO_CREATE_DONATIONS=False
```

Edge cases the regex handles:
- `\bicg\b` = word boundary, so "ICG donation - John" matches but "ricgardo" doesn't.
- Case-insensitive.
- Common typos / variants like "ICG-donation", "Don. ICG", "Donation ICG/Bhanu" — all match because `\b` treats `-`, `/`, `.`, space as boundaries.

The setting `DONATIONS_AUTO_CREATE` (default `True`) decides whether matched transactions immediately spawn a `Donation` row or sit in `status=review` for a treasurer to one-click approve. Start with `True` to make the feature actually save time; treasurer can ignore wrong matches via the admin UI.

### Donation creation logic

When `_classify` returns `MATCHED` and `DONATIONS_AUTO_CREATE`:

```python
campaign = (
    DonationCampaign.objects.filter(is_active=True)
    .order_by('-created_at').first()
)
if campaign is None:
    txn.status = BankTransaction.STATUS_REVIEW
    return  # no active campaign — let admin pick one later
```

Then:

```python
with transaction.atomic():
    donation = Donation.objects.create(
        campaign=campaign,
        user=_match_user(txn.counterparty_iban, txn.counterparty_name),
        donor_name=txn.counterparty_name if not matched_user else '',
        amount=txn.amount,
        donated_on=txn.booked_on,
        note=_extract_note(txn.remittance),   # strip "ICG donation" prefix
        source='bank',
        logged_by=None,
    )
    txn.donation = donation
    txn.status = BankTransaction.STATUS_MATCHED
    txn.save(update_fields=['donation', 'status'])
```

`_match_user`:
1. If `counterparty_iban` is set, look up `User.iban` (does **not exist yet** — see Open Questions).
2. Else exact-match `counterparty_name` against `User.first_name + ' ' + User.last_name`, case-insensitive. Only return a hit if there is **exactly one** match — ambiguity → return `None` and store the name in `donor_name`.

Wrong matches are recoverable — admin can edit the Donation in the Django admin to fix the user/name, set `is_anonymous`, change the campaign, etc.

## Admin review UI

New staff-only page `/banking/transactions/` ([htmx-partial-writer] candidate). Lists `BankTransaction` rows newest-first, filterable by status. Each row:

- Date, amount (in green if credit), counterparty, remittance excerpt
- Status pill (New / Matched / Ignored / Needs review)
- Actions:
  - **Mark as donation** → opens a small inline form (campaign + user/name) → creates Donation + sets status MATCHED
  - **Ignore** → status IGNORED
  - **Unlink donation** (only on MATCHED) → nulls the FK and reverts status to REVIEW; doesn't delete the Donation (treasurer might want to keep the record)

Linked to from "Manage" nav under a new "Banking" item, staff-gated.

## Public surface

[apps/donations/templates/donations/partials/_donations_panel.html] picks up the new `Donation.source` field. Small pill next to auto-imported entries:

```html
{% if donation.source == 'bank' %}
  <span class="text-[10px] uppercase tracking-wide bg-stone-100 text-stone-500 px-1.5 py-0.5 rounded">auto</span>
{% endif %}
```

No other UI change — the donor wall + progress bar already pulls from `campaign.donations`, which now includes bank-sourced rows automatically.

## Implementation order

1. **GoCardless account setup** (out-of-code prerequisite) — sign up at bankaccountdata.gocardless.com, obtain secret_id + secret_key, confirm N26 is in the institutions list for BE.
2. **App scaffold** — `python manage.py startapp banking` in `apps/`, register in `INSTALLED_APPS`, add `'banking/'` URL include.
3. **Schema** — `BankLink`, `BankTransaction` models + migration; `Donation.source` field + migration in donations app.
4. **GoCardless client** — `apps/banking/services/gocardless.py` with the 6 functions. Unit tests with `requests-mock`.
5. **Linking views** — `/banking/link/` start + callback. Staff-only.
6. **Import command** — `python manage.py import_bank_transactions`, with `_classify` and the donation-creation path. Tests covering: positive credit with ICG → Donation; positive credit without ICG → ignored; negative amount → ignored; duplicate transaction_id → skip; no active campaign → REVIEW.
7. **Cron registration** — add the command URL endpoint (token-auth like `run_reminders_view`) and add to cron-job.org schedule. 6h cadence.
8. **Admin review page** — list + per-row actions. HTMX partials.
9. **Public-page badge** — small change to `_donations_panel.html`.
10. **Re-consent notification** — banner on admin nav when `consent_valid_until < now() + 14 days`, plus WhatsApp DM to staff via existing notifications service.

Each step is its own commit. Steps 1–6 are the load-bearing path; 7–10 layer on top.

## Open questions

1. **`User.iban` field?** Donor → User matching is dramatically better if members have stored their IBAN on their profile. Worth adding `iban = models.CharField(max_length=34, blank=True)` to User? Optional, opt-in. **Recommendation:** add it; it also helps future wallet-refund flows.
2. **Auto-create vs. queue-for-review?** Proposed default `DONATIONS_AUTO_CREATE=True`. If we don't trust the ICG filter at first, flip to `False` and let treasurer one-click approve from the review page until confidence builds. **Recommendation:** start `True` (the whole point of automation), with the review page as the safety net.
3. **Which campaign gets the donation when there are multiple active ones?** Current proposal: newest active. Alternative: parse a second token in the reference (e.g. "ICG-server-bhanu" → server campaign). **Recommendation:** newest active for v1; add reference parsing in v2 if treasurer reports mis-attributions.
4. **Show last-sync timestamp on the support page?** "Last bank import: 2 hours ago" — signals freshness to donors. Cheap to add. **Recommendation:** yes, small footer on the donations panel.
5. **What about the Revolut / PayPal "extra link" already on DonationSettings?** Out of scope — different APIs, different rate limits. If the club starts accepting via Revolut routinely, that's a follow-up using the same `BankLink` abstraction (Revolut Business has a transactions API).
6. **Retention / right-to-erasure.** GDPR Article 17 — if a member asks for their bank data to be deleted, what do we do? The IBAN is in `BankTransaction.raw` JSON too, not just the column. **Recommendation:** on erasure request, set `counterparty_name = '[redacted]'`, blank `counterparty_iban`, and replace `raw` with `{}`. Keep `amount` + `booked_on` for accounting integrity.
7. **GoCardless rate limits.** Free tier: 4 transactions fetches per account per day, 10 details/balances fetches per day. 6-hour cron is fine (4× a day). Document the ceiling.

## Risk / rollback

- **Schema is additive** in donations (one new optional field), all-new in banking. Migrations reversible without data loss.
- **Quiet failure** — if GoCardless is down or consent expires, the cron fails silently from a member's perspective; donations stop appearing on the wall until re-link. Mitigations: admin banner on consent < 14 days, cron failure logged + DM'd to staff, manual log form stays available as fallback.
- **Wrong auto-attribution** — `_match_user` matches the wrong member (two "John"s). Recoverable: treasurer edits the Donation, but the donor sees the wrong name on the wall for hours. Mitigation: only match when there is exactly one candidate, default to `donor_name` text otherwise.
- **Money on the wall that isn't a donation** — a non-donation transfer gets through the ICG filter by accident (e.g. a treasurer reimbursing themselves with "ICG-refund" in the memo). Mitigation: treasurer reviews the audit page weekly; "ignore" action reverses it cleanly (deletes the Donation, marks transaction IGNORED).
- **Privacy bug** — IBAN of a donor leaking into a public template. We never render `counterparty_iban` outside the staff admin page; only `donor_name` or `User.first_name` shows on the support page.

## What stays the same

- The off-app SEPA flow ([_how_to_donate.html](../../apps/donations/templates/donations/partials/_how_to_donate.html)) — IBAN, reference instruction, payment link. Untouched.
- Manual `log_donation_view` form — kept as the fallback path; admins can still type a row by hand for cash gifts or out-of-band transfers.
- `DonationCampaign`, `FundItem`, `DonationSettings` models. Untouched.
- The contributor wall layout. Auto-imported donations slot into the same component, with an "auto" pill.
