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
    """Canonicalise to '+<digits>' E.164: strip spaces/dashes/parens, enforce '+'.

    The inbound WhatsApp webhook stores '+'-prefixed, digits-only numbers, and
    the wa.me deep links the group share builds are digits-only — so a member who
    typed '+32 471 12 34 56' must be stored as '+32471123456' or those lookups
    miss them. We keep only the leading '+' and the digits.
    """
    phone = (raw or '').strip()
    if not phone:
        raise forms.ValidationError('WhatsApp number is required.')
    if not phone.startswith('+'):
        raise forms.ValidationError('Phone must start with + and country code, e.g. +32471123456')
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if not digits:
        raise forms.ValidationError('Phone must include digits, e.g. +32471123456')
    return '+' + digits


class CustomSignupForm(SignupForm):
    """Allauth signup form extended with a required WhatsApp number and GDPR consent.

    Phone is required because the next-stage WhatsApp integration relies on
    reaching every member — see design_handoff/PROGRESS.md and the BotEvent
    model in apps/notifications/models.py.
    
    GDPR consent fields are required to comply with Belgian GDPR regulations.
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

    privacy_policy_accepted = forms.BooleanField(
        required=True,
        label="I accept the Privacy Policy",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the Terms of Service",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    whatsapp_accepted = forms.BooleanField(
        required=False,
        label="I accept that WhatsApp is required to vote on polls",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        
        # Update or create UserConsent record with actual consent values
        from apps.gdpr.models import UserConsent
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            ip_address = self._get_client_ip(request) if request else None
        except Exception as e:
            logger.exception(f"Error getting client IP: {e}")
            ip_address = None
        
        try:
            # Use get_or_create + update instead of just create
            # This handles the case where the post_save signal already created a record
            consent, created = UserConsent.objects.get_or_create(user=user)
            
            # Update with actual consent values from form
            consent.privacy_policy_accepted = self.cleaned_data.get('privacy_policy_accepted', False)
            consent.terms_accepted = self.cleaned_data.get('terms_accepted', False)
            consent.whatsapp_accepted = self.cleaned_data.get('whatsapp_accepted', False)
            if ip_address:
                consent.ip_address = ip_address
            consent.save()
            
            logger.info(f"UserConsent {'created' if created else 'updated'} for user {user.id}")
        except Exception as e:
            logger.exception(f"Error creating/updating UserConsent: {e}")
            # Don't fail signup if consent creation fails
            pass
        
        return user

    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


ROLE_CHOICES = (
    ('batsman', 'Batsman'),
    ('bowler', 'Bowler'),
    ('allrounder', 'All-Rounder'),
)


class OnboardingForm(forms.ModelForm):
    """Post-signup wizard: full name + role.

    Phone is collected at signup via CustomSignupForm.
    A single `full_name` field is split into first_name / last_name on save.
    """

    full_name = forms.CharField(max_length=120, required=True, label='Full name')
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'role']

    def clean_full_name(self):
        name = (self.cleaned_data.get('full_name') or '').strip()
        if not name:
            raise forms.ValidationError('Full name is required.')
        return name

    def save(self, commit=True):
        user = super().save(commit=False)
        name = self.cleaned_data['full_name']
        first, _, last = name.partition(' ')
        user.first_name = first
        user.last_name = last.strip()
        if commit:
            user.save()
        return user


# Avatars are user-uploaded; cap the size and reject non-images so a stray
# upload can't fill Cloudinary storage or break the <img> render.
AVATAR_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _clean_avatar(image):
    """Validate an uploaded avatar: must be a real image and ≤ 5 MB.

    Returns the file unchanged (or None/unchanged when nothing new was
    uploaded — e.g. ClearableFileInput's keep/clear sentinels)."""
    if not image:
        return image
    size = getattr(image, 'size', None)
    if size is not None and size > AVATAR_MAX_BYTES:
        raise forms.ValidationError('Image must be 5 MB or smaller.')
    # Only validate freshly uploaded files (they expose image_data via Pillow);
    # an existing FieldFile already on the model has no content_type to check.
    content_type = getattr(image, 'content_type', None)
    if content_type is not None and not content_type.startswith('image/'):
        raise forms.ValidationError('Please upload an image file.')
    return image


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'role': forms.Select(
                attrs={'class': 'w-full p-2 border rounded'},
                choices=[('batsman', 'Batsman'), ('bowler', 'Bowler'), ('allrounder', 'All-Rounder')],
            ),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
            }),
        }

    def clean_avatar(self):
        return _clean_avatar(self.cleaned_data.get('avatar'))


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


class AvatarForm(forms.ModelForm):
    """Single-field profile-picture form for the settings-card upload flow."""

    class Meta:
        model = User
        fields = ['avatar']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'sr-only',
                'accept': 'image/*',
            }),
        }

    def clean_avatar(self):
        return _clean_avatar(self.cleaned_data.get('avatar'))
