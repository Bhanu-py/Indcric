#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent

User = get_user_model()

# Reset testuser123 consent to incomplete
user = User.objects.get(username='testuser123')
consent = UserConsent.objects.get(user=user)

print(f"\n{'='*80}")
print(f"BEFORE RESET:")
print(f"{'='*80}")
print(f"  privacy_policy_accepted: {consent.privacy_policy_accepted}")
print(f"  terms_accepted: {consent.terms_accepted}")
print(f"  whatsapp_accepted: {consent.whatsapp_accepted}")

# Reset to incomplete
consent.privacy_policy_accepted = False
consent.terms_accepted = False
consent.whatsapp_accepted = False
consent.save()

print(f"\n{'='*80}")
print(f"AFTER RESET:")
print(f"{'='*80}")
print(f"  privacy_policy_accepted: {consent.privacy_policy_accepted}")
print(f"  terms_accepted: {consent.terms_accepted}")
print(f"  whatsapp_accepted: {consent.whatsapp_accepted}")
print(f"  all_consents_accepted: {consent.all_consents_accepted}")
print(f"\n✓ User {user.username} consent reset to incomplete")
print(f"{'='*80}\n")
