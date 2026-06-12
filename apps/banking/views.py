"""Bank-link views — staff-only.

Flow:
  GET  /banking/link/                  -> ASPSP picker (banking/link.html)
  GET  /banking/link/start/?aspsp=...  -> POST /auth on Enable Banking,
                                          stash CSRF state in session,
                                          303 to the bank's SCA URL
  GET  /banking/link/callback/         -> verify state, POST /sessions,
                                          create/update BankLink

The transactions list page lands in a follow-up commit.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone as tz

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import BankLink
from .services import enable_banking
from .services.importer import import_all_links

logger = logging.getLogger(__name__)

# Belgian / EU PSD2 ceiling. Some ASPSPs accept up to 180 days; 90 is the
# safe default that every bank supports.
DEFAULT_CONSENT_DAYS = 90


@staff_member_required
def link_index(request):
    """ASPSP picker. Lists banks Enable Banking supports for our country so the
    treasurer can pick which one to connect. Sandbox apps see the Mock ASPSPs.

    The bank list is only fetched when the admin actually wants to add a link
    (via ?add=1 or when there are no active links yet). Every fetch is an
    Enable Banking API call, so we don't waste one on every page visit.
    """
    country = request.GET.get('country', 'BE')
    links = list(BankLink.objects.filter(is_active=True))
    want_picker = request.GET.get('add') == '1' or not links

    aspsps = []
    error = None
    if want_picker:
        try:
            aspsps = enable_banking.list_aspsps(country=country)
        except enable_banking.EnableBankingError as e:
            error = f"Could not list banks: {e}"
            logger.exception("Enable Banking list_aspsps failed")
        except RuntimeError as e:
            error = str(e)

    return render(request, 'banking/link.html', {
        'country': country,
        'aspsps': aspsps,
        'error': error,
        'links': links,
        'show_picker': want_picker,
    })


@staff_member_required
def link_start(request):
    """Mint a CSRF state, call POST /auth, redirect to the bank's SCA URL."""
    aspsp_name = request.GET.get('aspsp', '').strip()
    country = request.GET.get('country', 'BE').strip()
    if not aspsp_name:
        return HttpResponseBadRequest("Missing aspsp query param.")

    state = secrets.token_urlsafe(24)
    request.session['banking_link_state'] = state
    request.session['banking_link_aspsp'] = aspsp_name
    request.session['banking_link_country'] = country

    try:
        resp = enable_banking.start_session(
            aspsp_name=aspsp_name,
            country=country,
            redirect_url=settings.ENABLE_BANKING_REDIRECT_URL,
            state=state,
        )
    except (enable_banking.EnableBankingError, RuntimeError) as e:
        logger.exception("Enable Banking start_session failed")
        messages.error(request, f"Could not start bank link: {e}")
        return redirect('banking_link_index')

    redirect_url = resp.get('url')
    if not redirect_url:
        messages.error(request, "Bank returned no authorization URL.")
        return redirect('banking_link_index')
    return redirect(redirect_url)


@staff_member_required
def link_callback(request):
    """Receive the post-SCA redirect. Verify state, exchange code, save BankLink."""
    expected = request.session.pop('banking_link_state', None)
    aspsp_name = request.session.pop('banking_link_aspsp', '')
    request.session.pop('banking_link_country', None)

    received_state = request.GET.get('state')
    if not expected or received_state != expected:
        return HttpResponseBadRequest("Invalid or missing state — possible CSRF.")

    code = request.GET.get('code')
    if not code:
        err = request.GET.get('error') or 'no code returned'
        messages.error(request, f"Bank link failed: {err}")
        return redirect('banking_link_index')

    try:
        session = enable_banking.complete_session(code)
    except enable_banking.EnableBankingError as e:
        logger.exception("Enable Banking complete_session failed")
        messages.error(request, f"Could not complete bank link: {e}")
        return redirect('banking_link_index')

    accounts = session.get('accounts') or []
    if not accounts:
        messages.error(request, "No accounts returned by the bank — try again.")
        return redirect('banking_link_index')

    # Link the first account. A multi-account picker can come later if a club
    # ever links a treasury account that has sub-accounts attached.
    acc = accounts[0]
    account_uid = acc.get('uid') or acc.get('account_id') or ''
    iban = acc.get('account_id', {}).get('iban') if isinstance(acc.get('account_id'), dict) else acc.get('iban', '')
    iban = iban or ''
    consent_until = datetime.now(tz.utc) + timedelta(days=DEFAULT_CONSENT_DAYS)
    label = f"{aspsp_name} — {iban or account_uid[:10]}"

    link, _ = BankLink.objects.update_or_create(
        provider=BankLink.PROVIDER_ENABLE_BANKING,
        provider_account_id=account_uid,
        defaults={
            'label': label,
            'institution_id': aspsp_name,
            'iban': iban,
            'provider_session_id': session.get('session_id', ''),
            'consent_valid_until': consent_until,
            'is_active': True,
        },
    )
    messages.success(request, f"Linked {link.label} successfully.")
    return render(request, 'banking/link_success.html', {'link': link})


@staff_member_required
@require_POST
def run_import_now(request):
    """In-app manual trigger for staff — the "Run import now" button on the
    banking link page. Same import path as the cron endpoint, but auth via
    session + staff flag instead of the shared token.

    Returns the result partial when called via HTMX (the button case) so the
    page can swap a result panel inline without a full reload; JSON otherwise
    for any non-HTMX caller that wants a programmatic response.
    """
    try:
        summary = import_all_links()
        error = None
    except Exception as e:
        logger.exception("run_import_now: import_all_links failed")
        summary = {}
        error = str(e)

    if request.htmx:
        return render(request, 'banking/partials/_import_result.html', {
            'summary': summary,
            'error': error,
            'now': timezone.now(),
        })
    return JsonResponse({'ok': error is None, 'summary': summary, 'error': error})


@staff_member_required
def diagnose_transactions(request):
    """Diagnostic view — fetches transactions from every active BankLink with
    each Enable Banking transaction_status value in turn and reports how many
    rows came back per status, without storing anything.

    Use this to investigate the 'I made a transfer but fetched=0' case — a
    non-zero count under 'PDNG' (pending) means Enable Banking has the txn
    but our import filter is correctly skipping it until it books.

    Staff-only. Returns JSON.
    """
    from datetime import date, timedelta
    # 'BOTH' was rejected by Enable Banking with 422 (valid values are
    # BOOK / CNCL / HOLD / OTHR / PDNG). Stick to BOOK + PDNG — that covers
    # the diagnosis case ('is the transfer booked yet, or still pending?')
    # without burning extra rate-limit budget on a value EB won't accept.
    statuses = ['BOOK', 'PDNG']
    date_from = date.today() - timedelta(days=7)

    out = {'date_from': date_from.isoformat(), 'links': []}
    for link in BankLink.objects.filter(is_active=True):
        per_status = {}
        for s in statuses:
            try:
                txns = list(enable_banking.get_transactions(
                    account_id=link.provider_account_id,
                    date_from=date_from,
                    transaction_status=s,
                ))
                per_status[s] = {
                    'count': len(txns),
                    'sample': [
                        {
                            'booked_on': str(t.booked_on),
                            'amount': str(t.amount),
                            'name': t.counterparty_name,
                            'remittance': t.remittance[:80],
                        }
                        for t in txns[:5]
                    ],
                }
            except enable_banking.EnableBankingError as e:
                per_status[s] = {'error': f"HTTP {e.status}: {e.body[:200]}"}
        out['links'].append({
            'id': link.id,
            'label': link.label,
            'iban': link.iban,
            'per_status': per_status,
        })
    return JsonResponse(out, json_dumps_params={'indent': 2})


@csrf_exempt
def run_import_view(request):
    """Cron-callable bank import. Token-authed via ?token=$BOT_WEBHOOK_TOKEN.

    Mirrors notifications.views.run_reminders_view — same shared secret so
    cron-job.org needs one token across both endpoints. Returns a JSON
    counts summary; non-2xx on auth failure so a failing cron alerts loudly.

    Suggested cadence: every 6 hours. The importer is idempotent (dedupe on
    provider transaction_id), so more frequent calls are safe — just wasteful.
    """
    expected = getattr(settings, 'BOT_WEBHOOK_TOKEN', '')
    token = request.GET.get('token', '')
    if not expected or token != expected:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=401)

    try:
        summary = import_all_links()
    except Exception:
        logger.exception("run_import_view: import_all_links failed")
        return JsonResponse({'ok': False, 'error': 'import failed'}, status=500)

    return JsonResponse({'ok': True, 'summary': summary})
