from decimal import Decimal

from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


def _round_to_half(value):
    """Snap a rating to the nearest 0.5 step (0, 0.5, 1.0, ..., 5.0)."""
    if value in (None, ''):
        return value
    return Decimal(str(round(float(value) * 2) / 2))


def _normalize_phone(raw):
    """Strip whitespace, enforce leading '+', return canonical form."""
    phone = (raw or '').strip()
    if not phone:
        raise forms.ValidationError('WhatsApp number is required.')
    if not phone.startswith('+'):
        raise forms.ValidationError('Phone must start with + and country code, e.g. +32471123456')
    return phone


class CustomSignupForm(SignupForm):
    """Allauth signup form extended with a required WhatsApp number.

    Phone is required because the next-stage WhatsApp integration relies on
    reaching every member — see design_handoff/PROGRESS.md and the BotEvent
    model in apps/notifications/models.py.
    """

    phone = forms.CharField(
        max_length=20,
        required=True,
        label='WhatsApp number',
        help_text='International format, e.g. +32471123456',
        widget=forms.TextInput(attrs={
            'placeholder': '+32471123456',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        }),
    )

    def clean_phone(self):
        phone = _normalize_phone(self.cleaned_data.get('phone'))
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This number is already registered.')
        return phone

    def save(self, request):
        user = super().save(request)
        user.phone = self.cleaned_data['phone']
        user.save(update_fields=['phone'])
        return user


ROLE_CHOICES = (
    ('batsman', 'Batsman'),
    ('bowler', 'Bowler'),
    ('allrounder', 'All-Rounder'),
)


class OnboardingForm(forms.ModelForm):
    """Post-signup wizard: full name + role + skill ratings.

    Phone is collected at signup via CustomSignupForm.
    A single `full_name` field is split into first_name / last_name on save.
    """

    full_name = forms.CharField(max_length=120, required=True, label='Full name')
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'role', 'batting_rating', 'bowling_rating', 'fielding_rating']

    def clean_full_name(self):
        name = (self.cleaned_data.get('full_name') or '').strip()
        if not name:
            raise forms.ValidationError('Full name is required.')
        return name

    def clean_batting_rating(self):
        return _round_to_half(self.cleaned_data.get('batting_rating'))

    def clean_bowling_rating(self):
        return _round_to_half(self.cleaned_data.get('bowling_rating'))

    def clean_fielding_rating(self):
        return _round_to_half(self.cleaned_data.get('fielding_rating'))

    def save(self, commit=True):
        user = super().save(commit=False)
        name = self.cleaned_data['full_name']
        first, _, last = name.partition(' ')
        user.first_name = first
        user.last_name = last.strip()
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'batting_rating', 'bowling_rating', 'fielding_rating']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'role': forms.Select(
                attrs={'class': 'w-full p-2 border rounded'},
                choices=[('batsman', 'Batsman'), ('bowler', 'Bowler'), ('allrounder', 'All-Rounder')],
            ),
            'batting_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.5'}),
            'bowling_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.5'}),
            'fielding_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.5'}),
        }

    def clean_batting_rating(self):
        return _round_to_half(self.cleaned_data.get('batting_rating'))

    def clean_bowling_rating(self):
        return _round_to_half(self.cleaned_data.get('bowling_rating'))

    def clean_fielding_rating(self):
        return _round_to_half(self.cleaned_data.get('fielding_rating'))


class EmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded'}),
        }


class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
        }


class PhoneForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded',
                'placeholder': '+32471123456',
                'autocomplete': 'tel',
                'inputmode': 'tel',
            }),
        }

    def clean_phone(self):
        phone = _normalize_phone(self.cleaned_data.get('phone'))
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This number is already registered to another account.')
        return phone
