from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


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


class OnboardingForm(forms.ModelForm):
    """Post-signup step that captures playing role.

    Phone is collected at signup via CustomSignupForm, so it's not asked here.
    """

    class Meta:
        model = User
        fields = ['role']
        widgets = {
            'role': forms.Select(
                attrs={'class': 'w-full p-2 border rounded'},
                choices=[('batsman', 'Batsman'), ('bowler', 'Bowler'), ('allrounder', 'All-Rounder')],
            ),
        }


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
            'batting_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.1'}),
            'bowling_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.1'}),
            'fielding_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.1'}),
        }


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
