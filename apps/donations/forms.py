from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model

from .models import Donation

User = get_user_model()


class DonationForm(forms.ModelForm):
    """Staff-facing form to log a received donation. A donation is attributed to
    either a known member, a free-text external name, or marked anonymous."""

    class Meta:
        model = Donation
        fields = ['user', 'donor_name', 'amount', 'donated_on', 'is_anonymous', 'note']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'donor_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'External donor name',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input', 'inputmode': 'decimal', 'step': '0.01',
                'min': '0.01', 'placeholder': '0.00',
            }),
            'donated_on': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'note': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Optional note (e.g. "for new balls")',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by(
            'first_name', 'username'
        )
        self.fields['user'].required = False
        self.fields['user'].empty_label = "— Member (optional) —"

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= Decimal('0'):
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('user') and not cleaned.get('donor_name') and not cleaned.get('is_anonymous'):
            raise forms.ValidationError(
                "Pick a member, enter a donor name, or mark the donation anonymous."
            )
        return cleaned
