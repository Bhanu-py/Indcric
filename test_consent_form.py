#!/usr/bin/env python
"""
Test script to verify checkbox handling in consent_accept_view
Simulates what happens when user submits the consent form.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from apps.gdpr.views import consent_accept_view
from django.contrib.auth.middleware import AuthenticationMiddleware
import json

User = get_user_model()

# Get test user
user = User.objects.get(username='testuser123')

print(f"\n{'='*80}")
print(f"TEST: Simulating checkbox form submission")
print(f"{'='*80}\n")

# Create a fake request
factory = RequestFactory()

# Test Case 1: User checks Privacy + Terms, leaves WhatsApp unchecked
print("TEST CASE 1: Privacy ✓, Terms ✓, WhatsApp ☐")
print("-" * 80)

request = factory.post('/gdpr/consent/accept/', {
    'privacy_policy_accepted': 'on',  # Checked
    'terms_accepted': 'on',            # Checked
    # whatsapp_accepted is NOT in POST (because unchecked)
})

# Add session and auth middleware
middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

# Add user to request
request.user = user

# Make it look like AJAX
request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

# Call the view
response = consent_accept_view(request)

# Check response
response_data = json.loads(response.content)
print(f"Response: {response_data}")

# Check what was saved in database
consent = UserConsent.objects.get(user=user)
print(f"\nDatabase values after submission:")
print(f"  privacy_policy_accepted: {consent.privacy_policy_accepted}")
print(f"  terms_accepted: {consent.terms_accepted}")
print(f"  whatsapp_accepted: {consent.whatsapp_accepted}")
print(f"  all_consents_accepted: {consent.all_consents_accepted}")

if consent.privacy_policy_accepted and consent.terms_accepted and not consent.whatsapp_accepted:
    print(f"\n✅ SUCCESS: Checkbox handling is working correctly!")
    print(f"   Privacy: True, Terms: True, WhatsApp: False (optional)")
else:
    print(f"\n❌ FAILED: Values not saved correctly")
    print(f"   Expected: Privacy=True, Terms=True, WhatsApp=False")
    print(f"   Got: Privacy={consent.privacy_policy_accepted}, Terms={consent.terms_accepted}, WhatsApp={consent.whatsapp_accepted}")

print(f"\n{'='*80}\n")

# Test Case 2: All checked
print("TEST CASE 2: Privacy ✓, Terms ✓, WhatsApp ✓")
print("-" * 80)

# Reset
consent.privacy_policy_accepted = False
consent.terms_accepted = False
consent.whatsapp_accepted = False
consent.save()

request = factory.post('/gdpr/consent/accept/', {
    'privacy_policy_accepted': 'on',
    'terms_accepted': 'on',
    'whatsapp_accepted': 'on',  # This one IS checked
})

middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

request.user = user
request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

response = consent_accept_view(request)
response_data = json.loads(response.content)
print(f"Response: {response_data}")

consent = UserConsent.objects.get(user=user)
print(f"\nDatabase values after submission:")
print(f"  privacy_policy_accepted: {consent.privacy_policy_accepted}")
print(f"  terms_accepted: {consent.terms_accepted}")
print(f"  whatsapp_accepted: {consent.whatsapp_accepted}")
print(f"  all_consents_accepted: {consent.all_consents_accepted}")

if consent.privacy_policy_accepted and consent.terms_accepted and consent.whatsapp_accepted:
    print(f"\n✅ SUCCESS: All fields saved correctly!")
else:
    print(f"\n❌ FAILED: Values not saved correctly")

print(f"\n{'='*80}\n")
