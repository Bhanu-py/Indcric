#!/usr/bin/env python
"""
Test script to diagnose email sending issues with Brevo/anymail.
Run with: python test_email_send.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

print("=" * 60)
print("EMAIL CONFIGURATION DIAGNOSTIC")
print("=" * 60)

# Check settings
print(f"\n1. EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"2. DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"3. DEBUG: {settings.DEBUG}")

# Check Brevo configuration
if hasattr(settings, 'ANYMAIL'):
    print(f"4. ANYMAIL config exists: {bool(settings.ANYMAIL)}")
    print(f"5. ANYMAIL keys: {list(settings.ANYMAIL.keys())}")
else:
    print("4. ANYMAIL config: NOT FOUND")

# Test email sending
print("\n" + "=" * 60)
print("TESTING EMAIL SEND")
print("=" * 60)

test_email = "test@example.com"
subject = "[IndCric] Test Email - Diagnostic"
message = "This is a test email from the diagnostic script."

try:
    print(f"\nSending test email to: {test_email}")
    result = send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [test_email],
        fail_silently=False,
    )
    print(f"✅ Email sent successfully! Result: {result}")
except Exception as e:
    print(f"❌ Email send failed!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
