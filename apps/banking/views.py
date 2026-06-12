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
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render

from .models import BankLink
from .services import enable_banking

logger = logging.getLogger(__name__)

# Belgian / EU PSD2 ceiling. Some ASPSPs accept up to 180 days; 90 is the
# safe default that every bank supports.
DEFAULT_CONSENT_DAYS = 90


@staff_member_required
def link_index(request):
    """ASPSP picker. Lists banks Enable Banking supports for our country so the
    treasurer can pick which one to connect. Sandbox apps see the Mock ASPSPs."""
    country = request.GET.get('country', 'BE')
    aspsps = []
    error = None
    try:
        aspsps = enable_banking.list_aspsps(country=country)
    except enable_banking.EnableBankingError as e:
        error = f"Could not list banks: {e}"
        logger.exception("Enable Banking list_aspsps failed")
    except RuntimeError as e:
        error = str(e)

    links = list(BankLink.objects.filter(is_active=True))
    return render(request, 'banking/link.html', {
        'country': country,
        'aspsps': aspsps,
        'error': error,
        'links': links,
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
