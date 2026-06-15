from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.banking.models import BankTransaction
from .forms import DonationForm, SelfDonationForm
from .models import Donation, DonationCampaign, DonationSettings, DonorLink


def _blank_form(user):
    """Full form for staff (log for anyone), self-service form for members."""
    return DonationForm() if user.is_staff else SelfDonationForm()


def support_view(request):
    """Public 'Support the club' page.

    Layout, top to bottom:
      1. Active specific fundraisers (transient drives with goals)
      2. General Donations (always-on, seeded; sits last among active rows)
      3. Previous fundraisers (closed specific drives, collapsed history)

    Logged-in members get an inline log-donation form on every still-open card
    (staff can log for anyone; members log their own). Closed drives drop the
    log form — the donation window is over."""
    # Specific fundraisers first (newest at the top), General Donations last as
    # the always-on catch-all. is_default sorts False -> True, so the default
    # row naturally floats to the bottom regardless of when it was created.
    active_campaigns = list(
        DonationCampaign.objects
        .filter(is_active=True)
        .prefetch_related('fund_items', 'donations__user')
        .order_by('is_default', '-created_at')
    )
    # Closed specific drives — historical record so /support/ shows the club's
    # past pushes (transparency + thank-you wall preserved). General Donations
    # never lands here; it's always active by definition.
    closed_campaigns = list(
        DonationCampaign.objects
        .filter(is_active=False, is_default=False)
        .prefetch_related('fund_items', 'donations__user')
        .order_by('-created_at')
    )
    # Pull out the always-on General Donations row so the template can render
    # its blurb + fund_items as a static 'why we ask for support' block above
    # the campaign cards. Same object stays in active_campaigns — the card
    # body just skips the duplicated blurb/items when is_default.
    general_donations = next((c for c in active_campaigns if c.is_default), None)

    context = {
        'active_campaigns': active_campaigns,
        'closed_campaigns': closed_campaigns,
        'general_donations': general_donations,
        'donation_settings': DonationSettings.objects.first(),
        'form': _blank_form(request.user) if request.user.is_authenticated else None,
    }
    return render(request, 'donations/support.html', context)


@login_required
def log_donation_view(request, campaign_id):
    """Log a received donation; HTMX-swaps the fundraiser body. Staff use the
    full form (any member / external name / anonymous); members self-log, always
    attributed to themselves so they can't claim someone else's gift."""
    campaign = get_object_or_404(DonationCampaign, id=campaign_id)
    if request.method != 'POST':
        return redirect('support')

    is_staff = request.user.is_staff
    form = DonationForm(request.POST) if is_staff else SelfDonationForm(request.POST)
    just_logged = None
    if form.is_valid():
        donation = form.save(commit=False)
        donation.campaign = campaign
        donation.logged_by = request.user
        if not is_staff:
            donation.user = request.user   # members can only log their own
            donation.donor_name = ''
        donation.save()
        just_logged = donation
        if not request.htmx:
            messages.success(request, f"Logged €{donation.amount} from {donation.display_name}.")
            return redirect('support')
        form = _blank_form(request.user)  # fresh form for the next entry

    context = {
        'campaign': campaign,
        'donations': list(campaign.donations.select_related('user')),
        'donation_settings': DonationSettings.objects.first(),
        'form': form,
        'just_logged': just_logged,
        'can_log': True,
    }
    if request.htmx:
        return render(request, 'donations/partials/_donations_panel.html', context)
    return redirect('support')


def _unlinked_bank_donor_groups():
    """Distinct bank counterparties whose imported donation isn't linked to a
    member yet — grouped by IBAN/name with totals, largest first."""
    groups = {}
    txns = (
        BankTransaction.objects
        .filter(donation__isnull=False, donation__user__isnull=True)
        .select_related('donation')
    )
    for bt in txns:
        iban = (bt.counterparty_iban or '').strip()
        name = (bt.counterparty_name or '').strip()
        key = (iban.lower(), name.lower())
        g = groups.setdefault(key, {
            'iban': iban, 'name': name or '(no name on transfer)',
            'total': Decimal('0.00'), 'count': 0,
        })
        g['total'] += bt.donation.amount
        g['count'] += 1
    return sorted(groups.values(), key=lambda g: g['total'], reverse=True)


@staff_member_required
def link_donors_view(request):
    """Staff reconciliation: map an imported bank donor (IBAN/name) to a member.

    Creates a durable DonorLink and back-fills every existing unlinked donation
    from that counterparty; future imports auto-attribute via DonorLink.resolve()
    in the bank importer. IBAN is the match key when present, else exact name.
    """
    User = get_user_model()
    members = User.objects.filter(is_active=True).order_by('first_name', 'username')

    if request.method == 'POST':
        iban = (request.POST.get('iban') or '').strip()
        name = (request.POST.get('name') or '').strip()
        user = User.objects.filter(id=request.POST.get('user') or 0).first()
        if not user or not (iban or name):
            messages.error(request, "Pick a member to link this donor to.")
        else:
            with transaction.atomic():
                if iban:
                    DonorLink.objects.update_or_create(
                        counterparty_iban=iban,
                        defaults={'user': user, 'counterparty_name': name},
                    )
                else:
                    link = DonorLink.objects.filter(
                        counterparty_iban='', counterparty_name__iexact=name).first()
                    if link:
                        link.user = user
                        link.save(update_fields=['user'])
                    else:
                        DonorLink.objects.create(
                            counterparty_iban='', counterparty_name=name, user=user)
                bts = BankTransaction.objects.filter(
                    donation__isnull=False, donation__user__isnull=True)
                if iban:
                    bts = bts.filter(counterparty_iban__iexact=iban)
                else:
                    bts = bts.filter(counterparty_iban='', counterparty_name__iexact=name)
                ids = list(bts.values_list('donation_id', flat=True))
                Donation.objects.filter(id__in=ids).update(user=user)
            messages.success(
                request,
                f"Linked {len(ids)} donation{'' if len(ids) == 1 else 's'} to "
                f"{user.get_full_name() or user.username}.")
        if request.htmx:
            return render(request, 'donations/partials/_donor_link_rows.html',
                          {'groups': _unlinked_bank_donor_groups(), 'members': members})
        return redirect('link-donors')

    return render(request, 'donations/link_donors.html',
                  {'groups': _unlinked_bank_donor_groups(), 'members': members})
