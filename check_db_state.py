#!/usr/bin/env python
"""Check the current state of consent in database."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
os.environ['DEBUG'] = 'True'
os.environ['BREVO_API_KEY'] = 'test'

django.setup()

from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent

User = get_user_model()

print("\n" + "="*80)
print("CURRENT CONSENT STATE IN DATABASE")
print("="*80 + "\n")

# Get the user
try:
    user = User.objects.get(username='testuser123')
except User.DoesNotExist:
    print("User 'testuser123' not found!")
    exit(1)

print(f"User: {user.username}")
print(f"User ID: {user.id}\n")

# Check consent
try:
    consent = UserConsent.objects.get(user=user)
    print(f"UserConsent found:")
    print(f"  - privacy_policy_accepted: {consent.privacy_policy_accepted}")
    print(f"  - terms_accepted: {consent.terms_accepted}")
    print(f"  - whatsapp_accepted: {consent.whatsapp_accepted}")
    print(f"  - all_consents_accepted: {consent.all_consents_accepted}")
    print()
    
    if consent.all_consents_accepted:
        print("[ERROR] Consent is still marked as COMPLETE!")
        print("Database reset may not have worked.")
    else:
        print("[OK] Consent is marked as INCOMPLETE")
        print("Database state is correct.")
        print("\nThe issue must be in the context processor or template rendering.")
        
except UserConsent.DoesNotExist:
    print("[ERROR] No UserConsent record for this user!")

print("\n" + "="*80)
