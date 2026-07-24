from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ClubConsultationResponse
from .views import SUCCESS_MESSAGE

User = get_user_model()


class ClubConsultationTests(TestCase):
    def valid_payload(self, **overrides):
        payload = {
            "name": "Kural",
            "email": "Kural@example.com",
            "phone": "+32470000000",
            "connection": "Player",
            "proceed_choice": ClubConsultationResponse.PROCEED_YES,
            "membership_preference": ClubConsultationResponse.MEMBERSHIP_ANNUAL,
            "volunteering_choice": ClubConsultationResponse.VOLUNTEER_MAYBE,
            "responsibilities": ["website", "membership_registration"],
            "time_commitment": ClubConsultationResponse.TIME_MONTHLY,
            "comments": "Good idea.",
            "consent": "on",
        }
        payload.update(overrides)
        return payload

    def test_cricket_club_page_renders(self):
        response = self.client.get(reverse("club:cricket-club"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proposal to Establish a Cricket Club in Ghent")
        self.assertContains(response, "Request a membership reimbursement certificate")
        self.assertContains(response, "Submit consultation response")

    def test_consultation_submission_creates_response(self):
        response = self.client.post(reverse("club:cricket-club"), self.valid_payload(), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, SUCCESS_MESSAGE)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.email, "kural@example.com")
        self.assertEqual(consultation.responsibilities, ["website", "membership_registration"])

    def test_volunteer_details_are_required_for_yes_or_maybe(self):
        response = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(responsibilities=[], time_commitment=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose at least one responsibility.")
        self.assertContains(response, "Choose how much time you can contribute.")
        self.assertEqual(ClubConsultationResponse.objects.count(), 0)

    def test_no_volunteering_clears_hidden_detail_fields(self):
        response = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(
                volunteering_choice=ClubConsultationResponse.VOLUNTEER_NO,
                responsibilities=["website"],
                time_commitment=ClubConsultationResponse.TIME_WEEKLY,
            ),
        )

        self.assertEqual(response.status_code, 302)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.responsibilities, [])
        self.assertEqual(consultation.time_commitment, "")

    def test_authenticated_member_updates_existing_response(self):
        user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="x",
            first_name="Member",
        )
        self.client.force_login(user)

        first = self.client.post(reverse("club:cricket-club"), self.valid_payload(email="member@example.com"))
        second = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(
                email="member@example.com",
                proceed_choice=ClubConsultationResponse.PROCEED_MORE_INFO,
            ),
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(ClubConsultationResponse.objects.count(), 1)
        self.assertEqual(
            ClubConsultationResponse.objects.get().proceed_choice,
            ClubConsultationResponse.PROCEED_MORE_INFO,
        )
