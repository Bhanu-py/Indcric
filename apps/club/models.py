from django.conf import settings
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
    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_ANNUAL, "Annual membership"),
        (MEMBERSHIP_MONTHLY, "Monthly membership"),
        (MEMBERSHIP_PER_GAME, "Payment for each game or training session"),
        (MEMBERSHIP_COMBINED, "A combination of annual and occasional membership"),
    ]

    VOLUNTEER_YES = "yes"
    VOLUNTEER_NO = "no"
    VOLUNTEER_MAYBE = "maybe"
    VOLUNTEER_CHOICES = [
        (VOLUNTEER_YES, "Yes"),
        (VOLUNTEER_NO, "No"),
    ]

    RESPONSIBILITY_OTHER = "other"
    ROLE_DIRECTOR_ADMIN = "director_admin"
    ROLE_DIRECTOR_FINANCE = "director_finance"
    ROLE_DIRECTOR_MEMBERSHIP = "director_membership"
    ROLE_FACILITIES = "facilities"
    ROLE_WEBSITE = "website"
    ROLE_GENERAL_HELP = "general_help"
    ROLE_SUPPORT = "role_support"
    ROLE_MORE_INFO = "role_more_info"
    RESPONSIBILITY_CHOICES = [
        (ROLE_DIRECTOR_ADMIN, "Director – General Administration"),
        (ROLE_DIRECTOR_FINANCE, "Director – Finance and Treasurer"),
        (ROLE_DIRECTOR_MEMBERSHIP, "Director – Membership and External Relations"),
        (ROLE_FACILITIES, "Facilities and Booking Coordinator"),
        (ROLE_WEBSITE, "Website and Communication Coordinator"),
        (ROLE_GENERAL_HELP, "I am ready to do any help as requested"),
    ]
    ORGANIZATIONAL_ROLE_VALUES = [
        ROLE_DIRECTOR_ADMIN,
        ROLE_DIRECTOR_FINANCE,
        ROLE_DIRECTOR_MEMBERSHIP,
        ROLE_FACILITIES,
        ROLE_WEBSITE,
    ]
    DIRECTOR_ROLE_VALUES = [
        ROLE_DIRECTOR_ADMIN,
        ROLE_DIRECTOR_FINANCE,
        ROLE_DIRECTOR_MEMBERSHIP,
    ]

    ROLE_PRIMARY_YES = "yes"
    ROLE_PRIMARY_MAYBE = "maybe"
    ROLE_PRIMARY_SUPPORT = "support_only"
    ROLE_PRIMARY_CHOICES = [
        (ROLE_PRIMARY_YES, "Yes"),
        (ROLE_PRIMARY_MAYBE, "Maybe"),
        (ROLE_PRIMARY_SUPPORT, "No, I can only provide support"),
    ]

    STARTUP_OTHER = "other"
    STARTUP_FEDERATION = "federation_insurance"
    STARTUP_STAD_GENT = "stad_gent"
    STARTUP_MEMBERS = "potential_members"
    STARTUP_STATUTES = "statutes_bylaws"
    STARTUP_VZW = "vzw_research"
    STARTUP_DIRECTORS = "directors_address"
    STARTUP_BUDGET = "initial_budget"
    STARTUP_FOUNDING = "founding_meeting"
    STARTUP_FORMS = "registration_documents"
    STARTUP_ADMIN = "formation_admin"
    STARTUP_OCCASIONAL = "occasional_help"
    STARTUP_MORE_INFO = "startup_more_info"
    STARTUP_TASK_CHOICES = [
        (STARTUP_FEDERATION, "Contact the sports federation and collect registration and insurance information"),
        (STARTUP_STAD_GENT, "Communicate with Stad Gent about recognition, facilities, and possible support"),
        (STARTUP_MEMBERS, "Collect the details of people interested in becoming members"),
        (STARTUP_STATUTES, "Help draft the club statutes or bylaws"),
        (STARTUP_VZW, "Research the VZW registration requirements"),
        (STARTUP_BUDGET, "Help prepare the initial budget and membership-fee proposal"),
        (STARTUP_FORMS, "Help prepare registration forms and official documents"),
        (STARTUP_ADMIN, "Help with general administration during the formation process"),
        (STARTUP_OCCASIONAL, "I can help occasionally when needed"),
    ]
    STARTUP_RESULT_CHOICES = [
        (STARTUP_FEDERATION, "Sports federation and insurance"),
        (STARTUP_STAD_GENT, "Stad Gent communication"),
        (STARTUP_MEMBERS, "Potential member registration"),
        (STARTUP_STATUTES, "Statutes or bylaws"),
        (STARTUP_VZW, "VZW registration research"),
        (STARTUP_BUDGET, "Initial budget and membership fee"),
        (STARTUP_FORMS, "Registration forms and documents"),
        (STARTUP_ADMIN, "General formation support"),
    ]
    STARTUP_PRIMARY_YES = "yes"
    STARTUP_PRIMARY_SHARED = "shared"
    STARTUP_PRIMARY_OCCASIONAL = "occasional"
    STARTUP_PRIMARY_MORE_INFO = "more_info"
    STARTUP_PRIMARY_CHOICES = [
        (STARTUP_PRIMARY_YES, "Yes"),
        (STARTUP_PRIMARY_SHARED, "I can share responsibility with another person"),
        (STARTUP_PRIMARY_OCCASIONAL, "I can only provide occasional help"),
        (STARTUP_PRIMARY_MORE_INFO, "I need more information"),
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
    role_primary_responsibility = models.CharField(max_length=20, choices=ROLE_PRIMARY_CHOICES, blank=True)
    startup_tasks = models.JSONField(default=list, blank=True)
    startup_other_task = models.CharField(max_length=180, blank=True)
    startup_primary_responsibility = models.CharField(max_length=20, choices=STARTUP_PRIMARY_CHOICES, blank=True)
    TIME_WEEKLY = "weekly"
    TIME_MONTHLY = "monthly"
    TIME_SPECIFIC = "specific_task"
    TIME_OCCASIONAL = "occasional"
    TIME_CHOICES = [
        (TIME_WEEKLY, "A few hours each week"),
        (TIME_MONTHLY, "A few hours each month"),
        (TIME_SPECIFIC, "Only when a specific task is assigned"),
        (TIME_OCCASIONAL, "Only occasionally"),
    ]
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

    @property
    def selected_responsibility_labels(self):
        labels = dict(self.RESPONSIBILITY_CHOICES)
        return [labels[value] for value in self.responsibilities or [] if value in labels]

    @property
    def selected_startup_task_labels(self):
        labels = dict(self.STARTUP_TASK_CHOICES)
        return [labels[value] for value in self.startup_tasks or [] if value in labels]
