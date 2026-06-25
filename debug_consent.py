#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent

User = get_user_model()

# Get the test user
user = User.objects.get(username='testuser123')
print(f"\n{'='*80}")
print(f"User: {user.username}")
print(f"{'='*80}\n")

# Check consent
try:
    consent = UserConsent.objects.get(user=user)
    print(f"UserConsent found:")
    print(f"  - privacy_policy_accepted: {consent.privacy_policy_accepted}")
    print(f"  - terms_accepted: {consent.terms_accepted}")
    print(f"  - whatsapp_accepted: {consent.whatsapp_accepted}")
    print(f"  - all_consents_accepted: {consent.all_consents_accepted}")
    print(f"\n[CRITICAL] all_consents_accepted = {consent.all_consents_accepted}")
    print(f"[CRITICAL] This controls if modal shows: show_consent_modal = not all_consents_accepted = {not consent.all_consents_accepted}")
except UserConsent.DoesNotExist:
    print("ERROR: No UserConsent record found!")

print(f"\n{'='*80}\n")
