from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class DonationSettings(models.Model):
    """Club-wide donation details (single row). All donations — campaign-tied or
    not — go to this one bank account, shown once on the support page. Kept in
    the DB (admin), never hardcoded in source."""
    account_holder = models.CharField(max_length=120, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    payment_reference = models.CharField(
        max_length=120, blank=True,
        help_text="Reference donors should add, e.g. 'ICG donation + your name'.",
    )
    payment_link = models.URLField(blank=True, help_text="Optional extra link (Revolut/PayPal/etc.).")

    class Meta:
        verbose_name = "Donation settings"
        verbose_name_plural = "Donation settings"

    def __str__(self):
        return "Donation settings (club bank account)"


class DonationCampaign(models.Model):
    """A fundraising drive for the club — server costs, drinks, gear, etc.

    Money is collected OFF-APP (SEPA transfer to the club's bank account, held
    once in DonationSettings); this model only tracks the goal and the donations
    a treasurer logs, so the page can show transparent progress + a thank-you
    wall.
    """
    title = models.CharField(max_length=120)
    blurb = models.TextField(blank=True, help_text="The 'why' — what the money is for.")
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def raised(self):
        """Sum of all logged donations (mirrors the wallet ledger pattern)."""
        return self.donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def progress_pct(self):
        """Capped 0–100 integer percent of goal raised (0 if no goal set)."""
        if not self.goal_amount:
            return 0
        pct = (self.raised() / self.goal_amount) * 100
        return min(100, int(pct))

    def supporter_count(self):
        return self.donations.count()


class Donation(models.Model):
    """One donation received toward a campaign, logged by a staff treasurer."""
    campaign = models.ForeignKey(
        DonationCampaign, on_delete=models.CASCADE, related_name='donations'
    )
    # A known member (preferred) or a free-text name for outside donors.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='donations',
    )
    donor_name = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_anonymous = models.BooleanField(
        default=False, help_text="Hide the donor's name on the public wall."
    )
    note = models.CharField(max_length=200, blank=True)
    donated_on = models.DateField(default=timezone.localdate)
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donated_on', '-created_at']

    def __str__(self):
        return f"{self.display_name} — €{self.amount}"

    @property
    def display_name(self):
        if self.is_anonymous:
            return "Anonymous"
        if self.user_id:
            return self.user.first_name or self.user.username
        return self.donor_name or "Anonymous"


class FundItem(models.Model):
    """One line in a campaign's 'what your donation funds' breakdown. Editable
    per campaign so each drive shows its own purpose (server, beers, gear…)."""
    ICON_CHOICES = [
        ('server', 'Server / hosting'),
        ('db', 'Database'),
        ('cup', 'Drinks / snacks'),
        ('ball', 'Ball / bat / gear'),
        ('heart', 'General'),
    ]
    COLOR_CHOICES = [
        ('pitch', 'Blue'),
        ('sky', 'Sky'),
        ('amber', 'Amber'),
        ('emerald', 'Green'),
        ('red', 'Red'),
        ('stone', 'Grey'),
    ]
    campaign = models.ForeignKey(
        DonationCampaign, on_delete=models.CASCADE, related_name='fund_items'
    )
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=160, blank=True)
    icon = models.CharField(max_length=10, choices=ICON_CHOICES, default='heart')
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='pitch')
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower shows first.")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title
