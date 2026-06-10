from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Donation, DonationCampaign, DonationSettings

User = get_user_model()


class DonationCampaignModelTests(TestCase):
    def setUp(self):
        self.campaign = DonationCampaign.objects.create(
            title="Server fund", goal_amount=Decimal('300.00')
        )

    def test_raised_sums_donations(self):
        Donation.objects.create(campaign=self.campaign, donor_name="A", amount=Decimal('50.00'))
        Donation.objects.create(campaign=self.campaign, donor_name="B", amount=Decimal('25.50'))
        self.assertEqual(self.campaign.raised(), Decimal('75.50'))

    def test_raised_zero_when_empty(self):
        self.assertEqual(self.campaign.raised(), Decimal('0.00'))

    def test_progress_pct_capped_at_100(self):
        Donation.objects.create(campaign=self.campaign, donor_name="A", amount=Decimal('400.00'))
        self.assertEqual(self.campaign.progress_pct(), 100)

    def test_progress_pct_zero_with_no_goal(self):
        c = DonationCampaign.objects.create(title="No goal", goal_amount=Decimal('0.00'))
        Donation.objects.create(campaign=c, donor_name="A", amount=Decimal('10.00'))
        self.assertEqual(c.progress_pct(), 0)

    def test_display_name_anonymous_hides_identity(self):
        u = User.objects.create_user(username="rohit", first_name="Rohit", password="x")
        d = Donation.objects.create(
            campaign=self.campaign, user=u, amount=Decimal('10'), is_anonymous=True
        )
        self.assertEqual(d.display_name, "Anonymous")

    def test_display_name_prefers_first_name(self):
        u = User.objects.create_user(username="rohit", first_name="Rohit", password="x")
        d = Donation.objects.create(campaign=self.campaign, user=u, amount=Decimal('10'))
        self.assertEqual(d.display_name, "Rohit")


class SupportPageTests(TestCase):
    def setUp(self):
        self.campaign = DonationCampaign.objects.create(
            title="Server fund", goal_amount=Decimal('300.00'),
        )
        DonationSettings.objects.create(account_holder="ICG", iban="DE00 0000")
        self.staff = User.objects.create_user(username="boss", password="x", is_staff=True)
        self.member = User.objects.create_user(username="member", password="x")

    def test_support_page_public(self):
        resp = self.client.get(reverse('support'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Server fund")

    def test_staff_can_log_donation(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'donor_name': 'Guest', 'amount': '40.00', 'donated_on': '2026-06-10'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.campaign.donations.count(), 1)
        d = self.campaign.donations.first()
        self.assertEqual(d.amount, Decimal('40.00'))
        self.assertEqual(d.logged_by, self.staff)

    def test_log_donation_htmx_returns_panel(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'donor_name': 'Guest', 'amount': '40.00', 'donated_on': '2026-06-10'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Guest')
        self.assertContains(resp, 'Log a donation')

    def test_member_logs_own_donation(self):
        self.client.force_login(self.member)
        resp = self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'amount': '15.00', 'donated_on': '2026-06-10'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.campaign.donations.count(), 1)
        d = self.campaign.donations.first()
        self.assertEqual(d.user, self.member)        # auto-attributed to self
        self.assertEqual(d.logged_by, self.member)

    def test_member_cannot_attribute_to_another_name(self):
        """A member's posted donor_name is ignored — it's always their own gift."""
        self.client.force_login(self.member)
        self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'donor_name': 'Someone Else', 'amount': '15.00', 'donated_on': '2026-06-10'},
        )
        d = self.campaign.donations.first()
        self.assertEqual(d.user, self.member)
        self.assertEqual(d.donor_name, '')

    def test_anonymous_user_cannot_log(self):
        resp = self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'amount': '15.00'},
        )
        self.assertEqual(resp.status_code, 302)  # redirected to login
        self.assertEqual(self.campaign.donations.count(), 0)

    def test_zero_amount_rejected(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'donor_name': 'Guest', 'amount': '0', 'donated_on': '2026-06-10'},
        )
        self.assertEqual(self.campaign.donations.count(), 0)
