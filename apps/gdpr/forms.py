from django import forms
from .models import UserConsent


class ConsentForm(forms.ModelForm):
    """
    Form for collecting GDPR consent during signup and login.
    All three consents are required.
    """
    privacy_policy_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I accept the Privacy Policy"
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I accept the Terms of Service"
    )
    whatsapp_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I accept that WhatsApp is required for voting"
    )

    class Meta:
        model = UserConsent
        fields = [
            'privacy_policy_accepted',
            'terms_accepted',
            'whatsapp_accepted',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
