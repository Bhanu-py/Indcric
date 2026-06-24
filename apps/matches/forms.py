"""
Forms for match management and scoring.
"""

from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import TemporaryScoringAccess


class TemporaryScoringAccessForm(forms.ModelForm):
    """Form for granting temporary scoring access to a player."""
    
    DURATION_CHOICES = [
        (30, '30 minutes'),
        (60, '1 hour'),
        (120, '2 hours'),
        (180, '3 hours'),
        (300, '5 hours'),
        (0, 'Custom duration'),
    ]
    
    duration_minutes = forms.ChoiceField(
        choices=DURATION_CHOICES,
        initial=60,
        help_text='How long should this access last?'
    )
    
    custom_duration_minutes = forms.IntegerField(
        min_value=1,
        max_value=1440,  # 24 hours max
        required=False,
        help_text='Duration in minutes (if Custom is selected)'
    )

    class Meta:
        model = TemporaryScoringAccess
        fields = ['user', 'session', 'reason']
        widgets = {
            'session': forms.HiddenInput(),
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., Primary scorer unavailable'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].help_text = 'Select the player to grant scoring access'
        self.fields['session'].help_text = 'Select the session date'

    def clean(self):
        cleaned_data = super().clean()
        
        # Check for existing ACTIVE access
        user = cleaned_data.get('user')
        session = cleaned_data.get('session')
        
        if user and session:
            existing = TemporaryScoringAccess.objects.filter(
                user=user,
                session=session,
                is_active=True  # Only check for ACTIVE access
            ).exists()
            
            if existing and not self.instance.pk:  # Only check for new objects
                raise forms.ValidationError(
                    f'This player already has active scoring access for {session.name}'
                )
        
        # Calculate expires_at based on duration
        duration_choice = cleaned_data.get('duration_minutes')
        custom_duration = cleaned_data.get('custom_duration_minutes')
        
        if duration_choice == '0':  # Custom
            if not custom_duration:
                raise forms.ValidationError('Please specify a custom duration in minutes')
            duration_minutes = custom_duration
        else:
            try:
                duration_minutes = int(duration_choice)
            except (ValueError, TypeError):
                raise forms.ValidationError('Invalid duration selection')
        
        # Set expires_at
        cleaned_data['expires_at'] = timezone.now() + timedelta(minutes=duration_minutes)
        
        return cleaned_data

    def save(self, commit=True, granted_by=None):
        instance = super().save(commit=False)
        if granted_by:
            instance.granted_by = granted_by
        # Ensure expires_at is set from cleaned data
        if 'expires_at' in self.cleaned_data:
            instance.expires_at = self.cleaned_data['expires_at']
        if commit:
            instance.save()
        return instance
