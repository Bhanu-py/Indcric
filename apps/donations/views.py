from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DonationForm, SelfDonationForm
from .models import DonationCampaign, DonationSettings


def _blank_form(user):
    """Full form for staff (log for anyone), self-service form for members."""
    return DonationForm() if user.is_staff else SelfDonationForm()


def support_view(request):
    """Public 'Support the club' page — the club's standing donation causes and
    the one bank account up top, then the current fundraiser(s) as wrappable
    cards with goal progress + contributor wall. Logged-in members get an inline
    log-donation form (staff can log for anyone; members log their own)."""
    active_campaigns = list(
        DonationCampaign.objects
        .filter(is_active=True)
        .prefetch_related('fund_items', 'donations__user')
        .order_by('-created_at')
    )
    context = {
        'active_campaigns': active_campaigns,
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
