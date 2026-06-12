from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DonationForm, SelfDonationForm
from .models import DonationCampaign, DonationSettings


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
