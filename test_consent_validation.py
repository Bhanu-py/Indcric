#!/usr/bin/env python
"""
Test script to verify consent form validation works correctly
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
user = User.objects.get(username='testuser123')

print(f"\n{'='*80}")
print(f"TEST: Validation - Missing required fields")
print(f"{'='*80}\n")

# Reset consent
consent = UserConsent.objects.get(user=user)
consent.privacy_policy_accepted = False
consent.terms_accepted = False
consent.whatsapp_accepted = False
consent.save()

# Test Case 1: Missing Privacy Policy
print("TEST CASE 1: Only Terms checked (Privacy missing)")
print("-" * 80)

factory = RequestFactory()
request = factory.post('/gdpr/consent/accept/', {
    # 'privacy_policy_accepted': 'on',  # MISSING!
    'terms_accepted': 'on',
})

middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

request.user = user
request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

response = consent_accept_view(request)
print(f"Response status: {response.status_code}")
response_data = json.loads(response.content)
print(f"Response: {response_data}")

if response.status_code == 400 and 'error' in response_data:
    print(f"✅ CORRECT: Form rejected with error message")
else:
    print(f"❌ FAILED: Should have rejected the form")

print(f"\n{'='*80}\n")

# Test Case 2: Missing Terms
print("TEST CASE 2: Only Privacy checked (Terms missing)")
print("-" * 80)

request = factory.post('/gdpr/consent/accept/', {
    'privacy_policy_accepted': 'on',
    # 'terms_accepted': 'on',  # MISSING!
})

middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

request.user = user
request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

response = consent_accept_view(request)
print(f"Response status: {response.status_code}")
response_data = json.loads(response.content)
print(f"Response: {response_data}")

if response.status_code == 400 and 'error' in response_data:
    print(f"✅ CORRECT: Form rejected with error message")
else:
    print(f"❌ FAILED: Should have rejected the form")

print(f"\n{'='*80}\n")
