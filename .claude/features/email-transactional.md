# Transactional Email — Brevo HTTPS API

**Status:** In progress — code merged, awaiting Brevo signup + env vars on Render
**Owner:** bhanu
**Created:** 2026-05-13

## Goal

Make `django-allauth` send real emails in production for:
- Mandatory email verification on signup
- Password reset
- Email change confirmation

Local dev keeps using Django's console backend so developers don't accidentally send real emails while testing.

## Why not Gmail SMTP

Originally configured Gmail SMTP (`smtp.gmail.com:587`). It works locally but produces gunicorn `WORKER TIMEOUT` on Render. Cause:

> Render free tier blocks all outbound SMTP (ports 25/465/587) — confirmed by [Render docs](https://render.com/docs/free). "Free instances can't send mail via SMTP."

Any SMTP provider (Gmail, Brevo SMTP, Mailgun SMTP) fails the same way on free tier. Workarounds:
- Upgrade to Render Starter ($7/mo) — SMTP unblocked
- **Use an HTTPS email API instead** ← chosen path

## Why Brevo

Compared free HTTPS-API options:

| Provider | Free quota | Sender requirement | Verdict |
|---|---|---|---|
| **Brevo** | 300/day = ~9k/month | Verify any single email (Gmail OK) | ✅ Chosen — no domain needed |
| Resend | 3,000/month | Verified domain (or limited to own email) | ❌ NGO has no domain yet |
| SendGrid | None (paid) | Domain or single sender | ❌ Not free |
| Mailjet | 200/day | Sender verification | ⚠️ Tighter cap than Brevo |

NGO scale = ~10–50 emails/month realistic. Brevo's 300/day is overkill margin.

## Implementation

### Code changes (committed in this branch)

| File | Change |
|---|---|
| `requirements.txt` | Added `django-anymail[brevo]` |
| `cric_core/settings.py` | `EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"` when `DEBUG=False`; console backend when `DEBUG=True`. Added `ANYMAIL = {"BREVO_API_KEY": os.getenv("BREVO_API_KEY")}`. `DEFAULT_FROM_EMAIL` env-driven. |
| `cric_core/settings.py` | Added allauth strictness: `ACCOUNT_EMAIL_REQUIRED = True`, `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`, `ACCOUNT_LOGIN_METHODS = {"username", "email"}`, `ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"` in prod. |
| (Neon DB) | `UPDATE django_site SET domain='indcric.onrender.com', name='IndCric' WHERE id=1` — so allauth verification links point at the deployed app, not `example.com`. |

### One-time Brevo setup (manual)

1. Sign up at brevo.com (free tier, no card).
2. Settings → Senders & IP → Senders → Add sender `IndCric <bhn4477@gmail.com>`. Click verification link.
3. Settings → SMTP & API → API Keys → Generate new key. Copy `xkeysib-...`.

### Render env vars

| Key | Value | Notes |
|---|---|---|
| `BREVO_API_KEY` | `xkeysib-...` | Secret. Set once in dashboard. |
| `DEFAULT_FROM_EMAIL` | `IndCric <bhn4477@gmail.com>` | Must match a verified Brevo sender exactly. |
| ~~`EMAIL_HOST_USER`~~ | — | Delete after switching off SMTP. |
| ~~`EMAIL_HOST_PASSWORD`~~ | — | Delete; also revoke the Gmail app password at myaccount.google.com/apppasswords. |

## Verification plan

After deploy:
1. Trigger password reset for `bhn4477@gmail.com` — expect email within ~30s.
2. Create a new account with a different email — expect verification email; cannot log in until clicked.
3. Check Brevo dashboard → Transactional → Logs — should show both messages as "Delivered".

## Failure modes to watch

| Symptom | Cause | Fix |
|---|---|---|
| 500 on signup/reset, logs show `WORKER TIMEOUT` + `sock.connect` | Still using SMTP backend (config not picked up) or `BREVO_API_KEY` missing | Confirm `EMAIL_BACKEND` in deployed settings; confirm env var set |
| Brevo dashboard shows "Rejected — sender not verified" | `DEFAULT_FROM_EMAIL` doesn't match a verified Brevo sender exactly | Match casing/spacing exactly: `IndCric <bhn4477@gmail.com>` |
| Emails delivered to spam | Free-tier Gmail sender reputation | Tolerable for NGO; switch to domain-verified sender when one is available |
| 401 from Brevo API in logs | API key revoked or wrong | Regenerate in Brevo, update env var |

## Future improvements

- Acquire a real domain (e.g. `indcric.org`), verify it in Brevo via DNS records (SPF/DKIM), then use `noreply@indcric.org` as sender — better deliverability, no Gmail dependency.
- Add Brevo delivery webhook to track bounces / spam complaints. Requires adding `anymail` to `INSTALLED_APPS` and wiring `anymail.urls`.
- Replace allauth's default email templates with branded HTML versions (override `templates/account/email/*.txt` and `.html`).
- For non-allauth notifications (session reminders, payment due), add a thin `cric.notifications` module that calls Django's `send_mail` — anymail backend handles delivery uniformly.

## Related

- [[whatsapp-bot]] — alternative notification channel for the same use cases. Email + WhatsApp can coexist; email for verification-style (audit-trail) messages, WhatsApp for reminders.
