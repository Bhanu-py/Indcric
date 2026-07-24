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
            "responsibilities": [
                ClubConsultationResponse.ROLE_DIRECTOR_ADMIN,
                ClubConsultationResponse.ROLE_WEBSITE,
            ],
            "startup_tasks": [
                ClubConsultationResponse.STARTUP_FEDERATION,
                ClubConsultationResponse.STARTUP_FORMS,
            ],
            "startup_primary_responsibility": ClubConsultationResponse.STARTUP_PRIMARY_SHARED,
            "question_vzw": "Who prepares the statutes?",
            "question_startup_tasks": "Who can contact the federation?",
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
        self.assertContains(response, "Interest in Organizational Roles")
        self.assertContains(response, "Volunteers Needed Before the Club Starts")
        self.assertContains(response, "Director – General Administration")
        self.assertNotContains(response, "Request a membership reimbursement certificate")
        self.assertNotContains(response, "I need more information before deciding.")
        self.assertNotContains(response, "Maybe, depending on the role and time required")
        self.assertNotContains(response, "I am not sure yet")
        self.assertNotContains(response, "I need more information")
        self.assertNotContains(response, "I can support one of these roles")
        self.assertNotContains(response, "Help identify three directors and a registered address")
        self.assertNotContains(response, "Help organize the founding meeting and voting")
        self.assertNotContains(response, "Serve as secretary")
        self.assertNotContains(response, "Maintain financial records")
        self.assertNotContains(response, "Prepare budgets and annual financial reports")
        self.assertNotContains(response, "Handle tax-related or administrative submissions")

    def test_authenticated_page_uses_member_account_not_manual_contact_fields(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("club:cricket-club"))

        self.assertContains(response, "Submitting as Kural")
        self.assertContains(response, "No separate name, email, or phone entry is needed.")
        self.assertContains(response, "Director – Finance and Treasurer")
        self.assertContains(response, "Which organizational role would you be willing to take on?")
        self.assertContains(response, "Which start-up tasks would you be willing to help with?")
        self.assertContains(response, "I am ready to do any help as requested")
        self.assertContains(response, "data-mobile-accordion")
        self.assertLess(
            response.content.decode().index("Submit your response"),
            response.content.decode().index("Votes so far"),
        )
        self.assertNotContains(response, "Would you be willing to take primary responsibility for this role?")
        self.assertNotContains(response, "I am not sure yet")
        self.assertNotContains(response, "I need more information")
        self.assertNotContains(response, "I can support one of these roles")
        self.assertNotContains(response, "Help identify three directors and a registered address")
        self.assertNotContains(response, "Help organize the founding meeting and voting")
        self.assertNotContains(response, "Other organizational role")
        self.assertNotContains(response, "Other start-up task")
        self.assertNotContains(response, "Time contribution")
        self.assertNotContains(response, "Serve as secretary")
        self.assertNotContains(response, "Maintain financial records")
        self.assertNotContains(response, "Prepare budgets and annual financial reports")
        self.assertNotContains(response, "Handle tax-related or administrative submissions")
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
        self.assertEqual(consultation.responsibilities, [
            ClubConsultationResponse.ROLE_DIRECTOR_ADMIN,
            ClubConsultationResponse.ROLE_WEBSITE,
        ])
        self.assertEqual(consultation.role_primary_responsibility, "")
        self.assertEqual(consultation.startup_tasks, [
            ClubConsultationResponse.STARTUP_FEDERATION,
            ClubConsultationResponse.STARTUP_FORMS,
        ])
        self.assertEqual(
            consultation.startup_primary_responsibility,
            ClubConsultationResponse.STARTUP_PRIMARY_SHARED,
        )
        self.assertEqual(consultation.volunteering_choice, ClubConsultationResponse.VOLUNTEER_YES)
        self.assertEqual(consultation.section_questions, {
            "question_vzw": "Who prepares the statutes?",
            "question_startup_tasks": "Who can contact the federation?",
        })

    def test_role_voting_is_optional(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(
                responsibilities=[],
                startup_tasks=[],
                startup_primary_responsibility="",
                question_vzw="",
                question_startup_tasks="",
            ),
        )

        self.assertEqual(response.status_code, 302)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.responsibilities, [])
        self.assertEqual(consultation.role_primary_responsibility, "")
        self.assertEqual(consultation.startup_tasks, [])
        self.assertEqual(consultation.startup_primary_responsibility, "")
        self.assertEqual(consultation.time_commitment, "")
        self.assertEqual(consultation.volunteering_choice, ClubConsultationResponse.VOLUNTEER_NO)

    def test_removed_role_and_startup_options_are_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(
                responsibilities=[ClubConsultationResponse.RESPONSIBILITY_OTHER],
                startup_tasks=[ClubConsultationResponse.STARTUP_OTHER],
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice")
        self.assertEqual(ClubConsultationResponse.objects.count(), 0)

    def test_authenticated_member_updates_existing_response(self):
        self.client.force_login(self.user)

        first = self.client.post(reverse("club:cricket-club"), self.valid_payload())
        second = self.client.post(
            reverse("club:cricket-club"),
            self.valid_payload(
                proceed_choice=ClubConsultationResponse.PROCEED_NO,
                responsibilities=[ClubConsultationResponse.ROLE_DIRECTOR_FINANCE],
                startup_tasks=[ClubConsultationResponse.STARTUP_BUDGET],
                startup_primary_responsibility=ClubConsultationResponse.STARTUP_PRIMARY_YES,
                question_vzw="",
                question_finance="Who files the accounts?",
                question_startup_tasks="",
            ),
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(ClubConsultationResponse.objects.count(), 1)
        consultation = ClubConsultationResponse.objects.get()
        self.assertEqual(consultation.proceed_choice, ClubConsultationResponse.PROCEED_NO)
        self.assertEqual(consultation.responsibilities, [ClubConsultationResponse.ROLE_DIRECTOR_FINANCE])
        self.assertEqual(consultation.role_primary_responsibility, "")
        self.assertEqual(consultation.startup_tasks, [ClubConsultationResponse.STARTUP_BUDGET])
        self.assertEqual(
            consultation.startup_primary_responsibility,
            ClubConsultationResponse.STARTUP_PRIMARY_YES,
        )
        self.assertEqual(consultation.section_questions, {"question_finance": "Who files the accounts?"})

    def test_public_page_shows_counts_without_names_or_question_text(self):
        other = User.objects.create_user(
            username="private",
            email="private@example.com",
            password="x",
            first_name="Private",
        )
        ClubConsultationResponse.objects.create(
            user=self.user,
            name="Kural",
            email="kural@example.com",
            proceed_choice=ClubConsultationResponse.PROCEED_YES,
            membership_preference=ClubConsultationResponse.MEMBERSHIP_ANNUAL,
            volunteering_choice=ClubConsultationResponse.VOLUNTEER_YES,
            responsibilities=[
                ClubConsultationResponse.ROLE_WEBSITE,
                ClubConsultationResponse.ROLE_DIRECTOR_FINANCE,
            ],
            startup_tasks=[ClubConsultationResponse.STARTUP_STATUTES],
            startup_primary_responsibility=ClubConsultationResponse.STARTUP_PRIMARY_SHARED,
            section_questions={"question_vzw": "Who prepares the statutes?"},
            consent=True,
        )
        ClubConsultationResponse.objects.create(
            user=other,
            name="Private Member",
            email="private@example.com",
            proceed_choice=ClubConsultationResponse.PROCEED_NO,
            membership_preference=ClubConsultationResponse.MEMBERSHIP_PER_GAME,
            volunteering_choice=ClubConsultationResponse.VOLUNTEER_NO,
            responsibilities=[],
            section_questions={},
            consent=True,
        )

        response = self.client.get(reverse("club:cricket-club"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Votes so far")
        self.assertContains(response, "Only counts are shown here")
        self.assertContains(response, "Question count by section")
        self.assertContains(response, "Start-up task volunteers")
        self.assertContains(response, "data-mobile-accordion")
        self.assertNotContains(response, "Private Member")
        self.assertNotContains(response, "private@example.com")
        self.assertNotContains(response, "Who prepares the statutes?")
        summary = response.context["summary"]
        self.assertEqual(summary["total_responses"], 2)
        self.assertEqual(summary["total_questions"], 1)
        self.assertEqual(summary["total_role_votes"], 2)
        self.assertEqual(summary["total_startup_task_votes"], 1)
        statutes_row = next(
            row for row in summary["startup_task_results"]
            if row["value"] == ClubConsultationResponse.STARTUP_STATUTES
        )
        self.assertEqual(statutes_row["interested"], 1)
        self.assertTrue(statutes_row["primary_available"])

    def test_staff_admin_summary_shows_member_votes_and_questions(self):
        staff = User.objects.create_user(username="staff", password="x", is_staff=True)
        ClubConsultationResponse.objects.create(
            user=self.user,
            name="Kural",
            email="kural@example.com",
            proceed_choice=ClubConsultationResponse.PROCEED_YES,
            membership_preference=ClubConsultationResponse.MEMBERSHIP_ANNUAL,
            volunteering_choice=ClubConsultationResponse.VOLUNTEER_YES,
            responsibilities=[ClubConsultationResponse.ROLE_WEBSITE],
            startup_tasks=[ClubConsultationResponse.STARTUP_STATUTES],
            startup_primary_responsibility=ClubConsultationResponse.STARTUP_PRIMARY_YES,
            section_questions={
                "question_vzw": "Who prepares the statutes?",
                "question_startup_tasks": "Who organizes the founding meeting?",
            },
            comments="Good idea.",
            consent=True,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("club:cricket-club-admin"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cricket club consultation admin")
        self.assertContains(response, "Club decision count")
        self.assertContains(response, "Question count by section")
        self.assertContains(response, "Interest in Organizational Roles")
        self.assertContains(response, "Start-up task volunteers")
        self.assertNotContains(response, "Role primary")
        self.assertContains(response, "Task primary")
        self.assertContains(response, "Kural")
        self.assertContains(response, "kural@example.com")
        self.assertContains(response, "Who prepares the statutes?")
        self.assertContains(response, "Who organizes the founding meeting?")

    def test_non_staff_cannot_open_consultation_admin_summary(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("club:cricket-club-admin"))

        self.assertEqual(response.status_code, 302)

    def test_anonymous_submission_redirects_to_login(self):
        response = self.client.post(reverse("club:cricket-club"), self.valid_payload())

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])
        self.assertEqual(ClubConsultationResponse.objects.count(), 0)
