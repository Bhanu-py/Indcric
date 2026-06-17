from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.banking.models import BankLink, BankTransaction
from .models import Donation, DonationCampaign, DonationSettings, DonorLink

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

    def test_member_cannot_log(self):
        """Members no longer self-log — donations import from the bank, so the
        log endpoint is staff-only and bounces non-staff."""
        self.client.force_login(self.member)
        resp = self.client.post(
            reverse('log-donation', args=[self.campaign.id]),
            {'amount': '15.00', 'donated_on': '2026-06-10'},
        )
        self.assertEqual(resp.status_code, 302)  # staff_member_required bounces non-staff
        self.assertEqual(self.campaign.donations.count(), 0)

    def test_member_does_not_see_log_form(self):
        self.client.force_login(self.member)
        resp = self.client.get(reverse('support'))
        # 'External donor name' is the staff form's donor field placeholder —
        # it only renders when the log form is present.
        self.assertNotContains(resp, 'External donor name')

    def test_staff_sees_log_form(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('support'))
        self.assertContains(resp, 'External donor name')

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


class DonorLinkTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="boss", password="x", is_staff=True)
        self.member = User.objects.create_user(username="ravi", first_name="Ravi", password="x")
        self.campaign = DonationCampaign.get_default()

    def _bank_donation(self, iban="", name="JOHN SMITH", txn_id="t1", amount="25.00"):
        d = Donation.objects.create(
            campaign=self.campaign, donor_name=name,
            amount=Decimal(amount), source=Donation.SOURCE_BANK,
        )
        link = BankLink.objects.create(label="Club")
        BankTransaction.objects.create(
            link=link, transaction_id=txn_id, booked_on=date(2026, 6, 1),
            amount=Decimal(amount), counterparty_iban=iban, counterparty_name=name,
            donation=d,
        )
        return d

    def test_resolve_by_iban(self):
        DonorLink.objects.create(user=self.member, counterparty_iban="BE68539", counterparty_name="J S")
        self.assertEqual(DonorLink.resolve("be68539", "anything"), self.member)  # case-insensitive

    def test_resolve_by_name_when_no_iban(self):
        DonorLink.objects.create(user=self.member, counterparty_iban="", counterparty_name="John Smith")
        self.assertEqual(DonorLink.resolve("", "JOHN SMITH"), self.member)

    def test_resolve_none_when_unknown(self):
        self.assertIsNone(DonorLink.resolve("BE999", "Nobody"))

    def test_link_view_creates_link_and_backfills(self):
        d = self._bank_donation(iban="BE68539", name="JOHN SMITH")
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('link-donors'),
            {'iban': 'BE68539', 'name': 'JOHN SMITH', 'user': self.member.id},
        )
        self.assertEqual(resp.status_code, 302)
        d.refresh_from_db()
        self.assertEqual(d.user, self.member)  # back-filled
        self.assertTrue(
            DonorLink.objects.filter(counterparty_iban="BE68539", user=self.member).exists()
        )

    def test_link_view_requires_staff(self):
        self.client.force_login(self.member)
        resp = self.client.get(reverse('link-donors'))
        self.assertEqual(resp.status_code, 302)  # staff_member_required bounces non-staff

    def test_importer_prefers_donorlink_over_fuzzy_match(self):
        from apps.banking.services.importer import _match_user
        DonorLink.objects.create(user=self.member, counterparty_iban="BE777", counterparty_name="Z")
        bt = BankTransaction(counterparty_iban="BE777", counterparty_name="Z")
        self.assertEqual(_match_user(bt), self.member)
