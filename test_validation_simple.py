#!/usr/bin/env python
"""
Simple validation test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent

User = get_user_model()
user = User.objects.get(username='testuser123')

print(f"\n{'='*80}")
print(f"VALIDATION TEST RESULTS")
print(f"{'='*80}\n")

# Test 1: Privacy + Terms (no WhatsApp) - SHOULD PASS
print("1. Privacy ✓, Terms ✓, WhatsApp ☐")
print("   Expected: SUCCESS (WhatsApp is optional)")

consent = UserConsent.objects.get(user=user)
consent.privacy_policy_accepted = True
consent.terms_accepted = True
consent.whatsapp_accepted = False
consent.save()

if consent.all_consents_accepted:
    print("   Result: ✅ PASS - all_consents_accepted = True\n")
else:
    print("   Result: ❌ FAIL - all_consents_accepted = False\n")

# Test 2: Privacy + WhatsApp (no Terms) - SHOULD FAIL
print("2. Privacy ✓, Terms ☐, WhatsApp ✓")
print("   Expected: FAIL (Terms is required)")

consent.privacy_policy_accepted = True
consent.terms_accepted = False
consent.whatsapp_accepted = True
consent.save()

if not consent.all_consents_accepted:
    print("   Result: ✅ PASS - all_consents_accepted = False (correctly invalid)\n")
else:
    print("   Result: ❌ FAIL - all_consents_accepted = True (should be False)\n")

# Test 3: Terms + WhatsApp (no Privacy) - SHOULD FAIL
print("3. Privacy ☐, Terms ✓, WhatsApp ✓")
print("   Expected: FAIL (Privacy is required)")

consent.privacy_policy_accepted = False
consent.terms_accepted = True
consent.whatsapp_accepted = True
consent.save()

if not consent.all_consents_accepted:
    print("   Result: ✅ PASS - all_consents_accepted = False (correctly invalid)\n")
else:
    print("   Result: ❌ FAIL - all_consents_accepted = True (should be False)\n")

# Test 4: All three - SHOULD PASS
print("4. Privacy ✓, Terms ✓, WhatsApp ✓")
print("   Expected: SUCCESS (all required fields + optional)")

consent.privacy_policy_accepted = True
consent.terms_accepted = True
consent.whatsapp_accepted = True
consent.save()

if consent.all_consents_accepted:
    print("   Result: ✅ PASS - all_consents_accepted = True\n")
else:
    print("   Result: ❌ FAIL - all_consents_accepted = False\n")

print(f"{'='*80}\n")
