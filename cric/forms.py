from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()

class OnboardingForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20,
        help_text='International format e.g. +32471123456',
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': '+32471123456'}),
    )

    class Meta:
        model = User
        fields = ['phone', 'role']
        widgets = {
            'role': forms.Select(
                attrs={'class': 'w-full p-2 border rounded'},
                choices=[('batsman', 'Batsman'), ('bowler', 'Bowler'), ('allrounder', 'All-Rounder')],
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not phone.startswith('+'):
            raise forms.ValidationError('Phone must start with + and country code, e.g. +32471123456')
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'batting_rating', 'bowling_rating', 'fielding_rating']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'role': forms.Select(attrs={'class': 'w-full p-2 border rounded'}, 
                              choices=[('batsman', 'Batsman'), ('bowler', 'Bowler'), ('allrounder', 'All-Rounder')]),
            'batting_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.1'}),
            'bowling_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.1'}),
            'fielding_rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': '0', 'max': '5', 'step': '0.1'}),
        }

class EmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded'})
        }

class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'})
        }