from django import forms

from .models import ClubConsultationResponse


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
    volunteering_choice = forms.ChoiceField(
        choices=ClubConsultationResponse.VOLUNTEER_CHOICES,
        widget=forms.RadioSelect(attrs={
            "class": "h-4 w-4 border-stone-300 text-pitch-600 focus:ring-pitch-500",
            "x-model": "volunteering",
        }),
        label="Would you be willing to join the organizing team?",
    )
    responsibilities = forms.MultipleChoiceField(
        choices=ClubConsultationResponse.RESPONSIBILITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            "class": "h-4 w-4 rounded border-stone-300 text-pitch-600 focus:ring-pitch-500",
        }),
        label="Which responsibilities would you be willing to take on?",
    )
    time_commitment = forms.ChoiceField(
        choices=ClubConsultationResponse.TIME_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={
            "class": "h-4 w-4 border-stone-300 text-pitch-600 focus:ring-pitch-500",
        }),
        label="How much time would you generally be able to contribute?",
    )
    consent = forms.BooleanField(
        required=True,
        label=(
            "I understand that the information I provide will be used only to assess "
            "interest in establishing the cricket club and to contact me regarding the organizing team."
        ),
        error_messages={"required": "Confirm the consultation data-use statement."},
    )

    class Meta:
        model = ClubConsultationResponse
        fields = [
            "name",
            "email",
            "phone",
            "connection",
            "proceed_choice",
            "membership_preference",
            "volunteering_choice",
            "responsibilities",
            "other_responsibility",
            "time_commitment",
            "comments",
            "consent",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "autocomplete": "name",
                "placeholder": "Your full name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "autocomplete": "email",
                "placeholder": "you@example.com",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "autocomplete": "tel",
                "placeholder": "Optional",
            }),
            "connection": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Player, parent, volunteer, supporter...",
            }),
            "other_responsibility": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Please describe",
            }),
            "comments": forms.Textarea(attrs={
                "class": "form-input min-h-[120px]",
                "rows": 5,
                "placeholder": "Optional comments or questions",
            }),
        }
        labels = {
            "name": "Name",
            "email": "Email address",
            "phone": "Telephone number",
            "connection": "Current connection to the cricket group",
            "other_responsibility": "Other responsibility",
            "comments": "Additional comments or questions",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if (
            user
            and getattr(user, "is_authenticated", False)
            and not self.is_bound
            and not getattr(self.instance, "pk", None)
        ):
            self.fields["name"].initial = user.get_full_name() or user.username
            self.fields["email"].initial = user.email
            if getattr(user, "phone", ""):
                self.fields["phone"].initial = user.phone

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()

    def clean_responsibilities(self):
        return list(self.cleaned_data.get("responsibilities") or [])

    def clean(self):
        cleaned = super().clean()
        volunteering_choice = cleaned.get("volunteering_choice")
        responsibilities = cleaned.get("responsibilities") or []
        other_responsibility = (cleaned.get("other_responsibility") or "").strip()

        if volunteering_choice == ClubConsultationResponse.VOLUNTEER_NO:
            cleaned["responsibilities"] = []
            cleaned["other_responsibility"] = ""
            cleaned["time_commitment"] = ""
            return cleaned

        if volunteering_choice in {
            ClubConsultationResponse.VOLUNTEER_YES,
            ClubConsultationResponse.VOLUNTEER_MAYBE,
        }:
            if not responsibilities:
                self.add_error("responsibilities", "Choose at least one responsibility.")
            if not cleaned.get("time_commitment"):
                self.add_error("time_commitment", "Choose how much time you can contribute.")

        if (
            ClubConsultationResponse.RESPONSIBILITY_OTHER in responsibilities
            and not other_responsibility
        ):
            self.add_error("other_responsibility", "Describe the other responsibility.")

        return cleaned

    def responsibility_rows(self):
        selected = set(self.data.getlist("responsibilities") if self.is_bound else self.initial.get("responsibilities", []))
        return [
            {"value": value, "label": label, "checked": value in selected}
            for value, label in ClubConsultationResponse.RESPONSIBILITY_CHOICES
        ]
