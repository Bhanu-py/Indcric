from django import forms

from .models import ClubConsultationResponse


STARTUP_PRIMARY_FORM_CHOICES = [
    choice for choice in ClubConsultationResponse.STARTUP_PRIMARY_CHOICES
    if choice[0] != ClubConsultationResponse.STARTUP_PRIMARY_MORE_INFO
]

SECTION_QUESTION_FIELDS = [
    ("question_why", "1. Why establish a formal club?"),
    ("question_vzw", "2. VZW structure"),
    ("question_board", "3. Board and organizing team"),
    ("question_address", "4. Official registered address"),
    ("question_statutes", "5. Statutes and internal rules"),
    ("question_membership", "6. Membership registration"),
    ("question_payment", "7. Membership-payment options"),
    ("question_insurance", "8. Member insurance"),
    ("question_mutuality", "9. Mutuality reimbursement"),
    ("question_facilities", "10. Sports facilities and possible support"),
    ("question_finance", "11. Financial administration"),
    ("question_responsibilities", "12. Interest in organizational roles"),
    ("question_startup_tasks", "13. Volunteers needed before the club starts"),
]


class ClubConsultationForm(forms.ModelForm):
    proceed_choice = forms.ChoiceField(
        choices=ClubConsultationResponse.PROCEED_CHOICES,
        widget=forms.RadioSelect(attrs={
            "class": "h-4 w-4 border-stone-300 text-pitch-600 focus:ring-pitch-500",
        }),
        label="Do you agree that we should proceed with establishing a formal cricket club in Ghent?",
    )
    membership_preference = forms.ChoiceField(
        choices=ClubConsultationResponse.MEMBERSHIP_CHOICES,
        widget=forms.RadioSelect(attrs={
            "class": "h-4 w-4 border-stone-300 text-pitch-600 focus:ring-pitch-500",
        }),
        label="Which membership-payment system would you prefer?",
    )
    responsibilities = forms.MultipleChoiceField(
        choices=ClubConsultationResponse.RESPONSIBILITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Which organizational role would you be willing to take on?",
    )
    role_primary_responsibility = forms.ChoiceField(
        choices=ClubConsultationResponse.ROLE_PRIMARY_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={
            "class": "h-4 w-4 border-stone-300 text-pitch-600 focus:ring-pitch-500",
        }),
        label="Would you be willing to take primary responsibility for this role?",
    )
    startup_tasks = forms.MultipleChoiceField(
        choices=ClubConsultationResponse.STARTUP_TASK_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Which start-up tasks would you be willing to help with?",
    )
    startup_primary_responsibility = forms.ChoiceField(
        choices=STARTUP_PRIMARY_FORM_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={
            "class": "h-4 w-4 border-stone-300 text-pitch-600 focus:ring-pitch-500",
        }),
        label="Would you be willing to take primary responsibility for one of these tasks?",
    )
    consent = forms.BooleanField(
        required=True,
        label=(
            "I understand that my response will be linked to my member account and used only "
            "to assess interest in establishing the cricket club and organizing responsibilities."
        ),
        error_messages={"required": "Confirm the consultation data-use statement."},
    )

    class Meta:
        model = ClubConsultationResponse
        fields = [
            "proceed_choice",
            "membership_preference",
            "responsibilities",
            "role_primary_responsibility",
            "startup_tasks",
            "startup_primary_responsibility",
            "comments",
            "consent",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={
                "class": "form-input min-h-[120px]",
                "rows": 5,
                "placeholder": "Optional general comments or questions",
            }),
        }
        labels = {
            "comments": "General comments or questions",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        section_questions = getattr(self.instance, "section_questions", None) or {}
        for field_name, label in SECTION_QUESTION_FIELDS:
            self.fields[field_name] = forms.CharField(
                required=False,
                label=f"Question about {label}",
                initial=section_questions.get(field_name, ""),
                widget=forms.Textarea(attrs={
                    "class": "form-input min-h-[92px]",
                    "rows": 3,
                    "placeholder": "Type your question about this section...",
                    "form": "club-consultation-form",
                }),
            )

    def clean_responsibilities(self):
        return list(self.cleaned_data.get("responsibilities") or [])

    def clean_startup_tasks(self):
        return list(self.cleaned_data.get("startup_tasks") or [])

    def save(self, commit=True):
        response = super().save(commit=False)
        response.volunteering_choice = (
            ClubConsultationResponse.VOLUNTEER_YES
            if self.cleaned_data.get("responsibilities") or self.cleaned_data.get("startup_tasks")
            else ClubConsultationResponse.VOLUNTEER_NO
        )
        response.other_responsibility = ""
        response.startup_other_task = ""
        response.section_questions = self.cleaned_section_questions()
        if commit:
            response.save()
        return response

    def cleaned_section_questions(self):
        questions = {}
        for field_name, label in SECTION_QUESTION_FIELDS:
            value = (self.cleaned_data.get(field_name) or "").strip()
            if value:
                questions[field_name] = value
        return questions

    def responsibility_rows(self):
        selected = set(
            self.data.getlist("responsibilities")
            if self.is_bound
            else self.initial.get("responsibilities", getattr(self.instance, "responsibilities", []) or [])
        )
        return [
            {"value": value, "label": label, "checked": value in selected}
            for value, label in ClubConsultationResponse.RESPONSIBILITY_CHOICES
        ]

    def startup_task_rows(self):
        selected = set(
            self.data.getlist("startup_tasks")
            if self.is_bound
            else self.initial.get("startup_tasks", getattr(self.instance, "startup_tasks", []) or [])
        )
        return [
            {"value": value, "label": label, "checked": value in selected}
            for value, label in ClubConsultationResponse.STARTUP_TASK_CHOICES
        ]
