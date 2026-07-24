from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ClubConsultationResponse(models.Model):
    PROCEED_YES = "yes"
    PROCEED_NO = "no"
    PROCEED_MORE_INFO = "more_info"
    PROCEED_CHOICES = [
        (PROCEED_YES, "Yes, I agree that we should start the club."),
        (PROCEED_NO, "No, I do not think we should start the club at this time."),
    ]

    MEMBERSHIP_ANNUAL = "annual"
    MEMBERSHIP_MONTHLY = "monthly"
    MEMBERSHIP_PER_GAME = "per_game"
    MEMBERSHIP_COMBINED = "combined"
    MEMBERSHIP_NOT_SURE = "not_sure"
    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_ANNUAL, "Annual membership"),
        (MEMBERSHIP_MONTHLY, "Monthly membership"),
        (MEMBERSHIP_PER_GAME, "Payment for each game or training session"),
        (MEMBERSHIP_COMBINED, "A combination of annual and occasional membership"),
        (MEMBERSHIP_NOT_SURE, "I am not sure yet"),
    ]

    VOLUNTEER_YES = "yes"
    VOLUNTEER_NO = "no"
    VOLUNTEER_MAYBE = "maybe"
    VOLUNTEER_CHOICES = [
        (VOLUNTEER_YES, "Yes"),
        (VOLUNTEER_NO, "No"),
    ]

    TIME_WEEKLY = "weekly"
    TIME_MONTHLY = "monthly"
    TIME_SPECIFIC = "specific_task"
    TIME_OCCASIONAL = "occasional"
    TIME_NOT_SURE = "not_sure"
    TIME_CHOICES = [
        (TIME_WEEKLY, "A few hours each week"),
        (TIME_MONTHLY, "A few hours each month"),
        (TIME_SPECIFIC, "Only when a specific task is assigned"),
        (TIME_OCCASIONAL, "Only occasionally"),
        (TIME_NOT_SURE, "I am not sure yet"),
    ]

    RESPONSIBILITY_OTHER = "other"
    RESPONSIBILITY_CHOICES = [
        ("director", "Serve as a director or board member"),
        ("registered_address", "Provide an official registered address"),
        ("statutes", "Help prepare the statutes and internal rules"),
        ("chairperson", "Serve as chairperson or general coordinator"),
        ("secretary", "Serve as secretary"),
        ("treasurer", "Serve as treasurer"),
        ("bank_account", "Manage the club bank account"),
        ("financial_records", "Maintain financial records"),
        ("budgets_reports", "Prepare budgets and annual financial reports"),
        ("tax_admin", "Handle tax-related or administrative submissions"),
        ("membership_registration", "Manage membership registration"),
        ("membership_payments", "Monitor membership payments"),
        ("membership_certificates", "Prepare membership certificates for mutuality reimbursement"),
        ("insurance_registration", "Coordinate insurance registration"),
        ("accident_documents", "Assist with accident-reporting documents"),
        ("facility_booking", "Book sports halls and cricket grounds"),
        ("city_communication", "Communicate with the City of Ghent"),
        ("federation_communication", "Communicate with Cricket Vlaanderen or another federation"),
        ("subsidies", "Apply for subsidies or reimbursements"),
        ("equipment", "Manage cricket equipment"),
        ("website", "Maintain the club website"),
        ("forms", "Manage registration and consultation forms"),
        ("emails", "Manage member emails and announcements"),
        ("privacy", "Assist with privacy and data protection"),
        ("volunteer_coordination", "Coordinate volunteers"),
        ("occasional_help", "Help occasionally without taking a permanent role"),
        (RESPONSIBILITY_OTHER, "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_consultation_responses",
    )
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(db_index=True, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    connection = models.CharField(max_length=160, blank=True)
    proceed_choice = models.CharField(max_length=20, choices=PROCEED_CHOICES)
    membership_preference = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES)
    volunteering_choice = models.CharField(max_length=20, choices=VOLUNTEER_CHOICES)
    responsibilities = models.JSONField(default=list, blank=True)
    other_responsibility = models.CharField(max_length=160, blank=True)
    time_commitment = models.CharField(max_length=20, choices=TIME_CHOICES, blank=True)
    section_questions = models.JSONField(default=dict, blank=True)
    comments = models.TextField(blank=True)
    consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        verbose_name = "club consultation response"
        verbose_name_plural = "club consultation responses"

    def __str__(self):
        return f"{self.name} - {self.get_proceed_choice_display()}"

    def clean(self):
        super().clean()
        responsibilities = self.responsibilities or []
        if self.RESPONSIBILITY_OTHER in responsibilities and not self.other_responsibility.strip():
            raise ValidationError({"other_responsibility": "Describe the other responsibility."})

    @property
    def selected_responsibility_labels(self):
        labels = dict(self.RESPONSIBILITY_CHOICES)
        selected = [labels.get(value, value) for value in self.responsibilities or []]
        if self.other_responsibility:
            selected.append(self.other_responsibility)
        return selected
