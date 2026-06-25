#!/usr/bin/env python
"""
Test the context processor logic
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent
from apps.gdpr.context_processors import gdpr_context
from django.test import RequestFactory
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

User = get_user_model()
user = User.objects.get(username='testuser123')

print(f"\n{'='*80}")
print(f"CONTEXT PROCESSOR TEST")
print(f"{'='*80}\n")

factory = RequestFactory()

# Scenario 1: Consent incomplete
print("SCENARIO 1: Consent incomplete (Privacy=F, Terms=F)")
print("-" * 80)

consent = UserConsent.objects.get(user=user)
consent.privacy_policy_accepted = False
consent.terms_accepted = False
consent.whatsapp_accepted = False
consent.save()

request = factory.get('/')
middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

request.user = user

context = gdpr_context(request)
print(f"  all_consents_accepted: {consent.all_consents_accepted}")
print(f"  show_consent_modal in context: {context['show_consent_modal']}")

if context['show_consent_modal'] == True:
    print(f"  ✅ CORRECT: Modal should show\n")
else:
    print(f"  ❌ WRONG: Modal should show but doesn't\n")

# Scenario 2: Consent complete
print("SCENARIO 2: Consent complete (Privacy=T, Terms=T, WhatsApp=F)")
print("-" * 80)

consent.privacy_policy_accepted = True
consent.terms_accepted = True
consent.whatsapp_accepted = False
consent.save()

request = factory.get('/')
middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

request.user = user

context = gdpr_context(request)
print(f"  all_consents_accepted: {consent.all_consents_accepted}")
print(f"  show_consent_modal in context: {context['show_consent_modal']}")

if context['show_consent_modal'] == False:
    print(f"  ✅ CORRECT: Modal should NOT show\n")
else:
    print(f"  ❌ WRONG: Modal should not show\n")

# Scenario 3: Partial consent
print("SCENARIO 3: Partial consent (Privacy=T, Terms=F)")
print("-" * 80)

consent.privacy_policy_accepted = True
consent.terms_accepted = False
consent.whatsapp_accepted = False
consent.save()

request = factory.get('/')
middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.session.save()

auth_middleware = AuthenticationMiddleware(lambda x: x)
auth_middleware.process_request(request)

request.user = user

context = gdpr_context(request)
print(f"  all_consents_accepted: {consent.all_consents_accepted}")
print(f"  show_consent_modal in context: {context['show_consent_modal']}")

if context['show_consent_modal'] == True:
    print(f"  ✅ CORRECT: Modal should show (Terms not accepted)\n")
else:
    print(f"  ❌ WRONG: Modal should show\n")

print(f"{'='*80}\n")
