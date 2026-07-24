from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ClubConsultationResponse
from .views import SUCCESS_MESSAGE

User = get_user_model()


class ClubConsultationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="kural",
            email="kural@example.com",
            password="x",
            first_name="Kural",
        )

    def valid_payload(self, **overrides):
        payload = {
            "proceed_choice": ClubConsultationResponse.PROCEED_YES,
            "membership_preference": ClubConsultationResponse.MEMBERSHIP_ANNUAL,
            "responsibilities": ["website", "membership_registration"],
            "time_commitment": ClubConsultationResponse.TIME_MONTHLY,
            "question_vzw": "Who prepares the statutes?",
            "comments": "Good idea.",
            "consent": "on",
        }
        payload.update(overrides)
        return payload

    def test_cricket_club_page_renders_public_information(self):
        response = self.client.get(reverse("club:cricket-club"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proposal to Establish a Cricket Club in Ghent")
        self.assertContains(response, "Page navigation")
        self.assertContains(response, "Sign in to vote")
        self.assertContains(response, "Ask a question about this section")
        self.assertNotContains(response, "Request a membership reimbursement certificate")
        self.assertNotContains(response, "I need more information before deciding.")
        self.assertNotContains(response, "Maybe, depending on the role and time required")

    def test_authenticated_page_uses_member_account_not_manual_contact_fields(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("club:cricket-club"))

        self.assertContains(response, "Submitting as Kural")
        self.assertContains(response, "No separate name, email, or phone entry is needed.")
        self.assertNotContains(response, "Your full name")
        self.assertNotContains(response, "you@example.com")

    def test_consultation_submission_creates_response_for_member(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("club:cricket-club"), self.valid_payload(), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, SUCCESS_MESSAGE)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.user, self.user)
        self.assertEqual(consultation.name, "Kural")
        self.assertEqual(consultation.email, "kural@example.com")
        self.assertEqual(consultation.responsibilities, ["website", "membership_registration"])
        self.assertEqual(consultation.volunteering_choice, ClubConsultationResponse.VOLUNTEER_YES)
        self.assertEqual(consultation.section_questions, {"question_vzw": "Who prepares the statutes?"})

    def test_role_voting_is_optional(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(responsibilities=[], time_commitment="", question_vzw=""),
        )

        self.assertEqual(response.status_code, 302)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.responsibilities, [])
        self.assertEqual(consultation.time_commitment, "")
        self.assertEqual(consultation.volunteering_choice, ClubConsultationResponse.VOLUNTEER_NO)

    def test_other_role_requires_description(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(responsibilities=["other"], other_responsibility=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Describe the other role or responsibility.")
        self.assertEqual(ClubConsultationResponse.objects.count(), 0)

    def test_authenticated_member_updates_existing_response(self):
        self.client.force_login(self.user)

        first = self.client.post(reverse("club:cricket-club"), self.valid_payload())
        second = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(
                proceed_choice=ClubConsultationResponse.PROCEED_NO,
                responsibilities=["treasurer"],
                question_vzw="",
                question_finance="Who files the accounts?",
            ),
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(ClubConsultationResponse.objects.count(), 1)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.proceed_choice, ClubConsultationResponse.PROCEED_NO)
        self.assertEqual(consultation.responsibilities, ["treasurer"])
        self.assertEqual(consultation.section_questions, {"question_finance": "Who files the accounts?"})

    def test_anonymous_submission_redirects_to_login(self):
        response = self.client.post(reverse("club:cricket-club"), self.valid_payload())

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])
        self.assertEqual(ClubConsultationResponse.objects.count(), 0)
