#!/usr/bin/env python
"""
Direct Brevo API test - bypass Django to test pure API connectivity.
Run with: python brevo_api_test.py
"""
import os
import requests

# Get API key from environment
API_KEY = os.getenv("BREVO_API_KEY", "")

if not API_KEY:
    print("❌ ERROR: BREVO_API_KEY environment variable not set!")
    print("Set it with: export BREVO_API_KEY='your-key-here'")
    exit(1)

print("=" * 70)
print("BREVO API DIRECT TEST")
print("=" * 70)

# Test 1: Check API connectivity
print("\n1️⃣ Testing Brevo API connectivity...")
headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}

try:
    response = requests.get(
        "https://api.brevo.com/v3/account",
        headers=headers,
        timeout=10,
        verify=False  # Disable SSL verification for testing
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Key is VALID")
        print(f"   Account: {data.get('email', 'N/A')}")
        print(f"   Company: {data.get('companyName', 'N/A')}")
        print(f"   Plan: {data.get('plan', 'N/A')}")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Connection Error: {str(e)}")
    exit(1)

# Test 2: Get sender list
print("\n2️⃣ Fetching verified senders...")
try:
    response = requests.get(
        "https://api.brevo.com/v3/senders",
        headers=headers,
        timeout=10,
        verify=False
    )
    
    if response.status_code == 200:
        senders = response.json().get("senders", [])
        if senders:
            print(f"✅ Found {len(senders)} verified sender(s):")
            for sender in senders:
                status = "✅ VERIFIED" if sender.get("isVerified") else "❌ NOT VERIFIED"
                print(f"   - {sender.get('email')} {status}")
        else:
            print(f"⚠️  No senders found - you need to verify a sender email in Brevo!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 3: Check contacts/domains
print("\n3️⃣ Checking email sending limits...")
try:
    response = requests.get(
        "https://api.brevo.com/v3/smtp/statistics",
        headers=headers,
        timeout=10,
        verify=False
    )
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ SMTP Statistics:")
        print(f"   Total sent: {stats.get('totalSent', 0)}")
        print(f"   Today sent: {stats.get('today', 0)}")
    else:
        print(f"⚠️ Could not fetch statistics: {response.status_code}")
        
except Exception as e:
    print(f"⚠️ Stats error: {str(e)}")

print("\n" + "=" * 70)
print("ACTIONS NEEDED:")
print("=" * 70)
print("""
1. Go to Brevo Dashboard: https://app.brevo.com
2. Click "Senders" in left menu
3. Check if indiancricket.ghent@gmail.com is VERIFIED
4. If NOT verified, click "Add sender" and complete verification
5. Once verified, test signup again

Note: For @gmail.com addresses, you may need SPF/DKIM records
configured in Gmail. Consider using a custom domain instead.
""")
print("=" * 70)
