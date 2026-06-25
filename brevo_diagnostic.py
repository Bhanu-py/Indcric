"""
Diagnostic script to test Brevo API connectivity and identify email delivery issues.
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')

import django
django.setup()

from django.conf import settings
from django.core.mail import send_mail
import logging

# Setup logging to see details
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("BREVO EMAIL DELIVERY DIAGNOSTIC")
print("="*70)

print(f"\n📧 EMAIL BACKEND: {settings.EMAIL_BACKEND}")
print(f"🔑 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"🐛 DEBUG MODE: {settings.DEBUG}")

# Check ANYMAIL config
if hasattr(settings, 'ANYMAIL'):
    print(f"✅ ANYMAIL config found")
    if 'BREVO_API_KEY' in settings.ANYMAIL:
        api_key = settings.ANYMAIL['BREVO_API_KEY']
        masked_key = api_key[:10] + '...' + api_key[-10:] if len(api_key) > 20 else '***'
        print(f"✅ BREVO_API_KEY exists: {masked_key}")
    else:
        print(f"❌ BREVO_API_KEY NOT in ANYMAIL config")
else:
    print(f"❌ ANYMAIL config NOT found - emails won't send to Brevo!")

# Test with anymail directly
print("\n" + "-"*70)
print("TESTING DIRECT BREVO API CALL")
print("-"*70)

try:
    from anymail.backends.brevo import EmailBackend as BrevoBackend
    
    backend = BrevoBackend()
    print("✅ Brevo backend imported successfully")
    
    # Try to create and send a test message
    from django.core.mail import EmailMessage
    
    msg = EmailMessage(
        subject="[IndCric] Test Email",
        body="This is a test email to verify Brevo delivery.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["test-delivery-check@example.com"],
    )
    
    print(f"\n📤 Attempting to send test email...")
    result = backend.send_messages([msg])
    
    if result == 1:
        print(f"✅ Email accepted by Brevo API (result={result})")
        print(f"⚠️  Note: This means Brevo accepted it, but doesn't guarantee delivery")
        print(f"   Check Brevo dashboard for bounce/delivery logs")
    else:
        print(f"❌ Brevo returned unexpected result: {result}")
        
except Exception as e:
    print(f"❌ Error testing Brevo backend:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TROUBLESHOOTING STEPS:")
print("="*70)
print("""
1. Check Brevo Dashboard:
   - Go to https://app.brevo.com/login
   - Check "Campaigns" > "Logs" for bounced/failed emails
   - Verify API key has "SMTP" and "Marketing" permissions
   
2. Check Email Address:
   - Ensure the test email address is valid (not @example.com)
   - Check if address is on Brevo's spam list
   
3. Check Sender Domain:
   - Brevo might require SPF/DKIM records for indiancricket.ghent@gmail.com
   - Check Brevo dashboard > Senders > Verification status
   
4. Check Rate Limits:
   - Free Brevo accounts have limits
   - Paid plans are required for higher volumes
""")
print("="*70 + "\n")
