#!/usr/bin/env python
"""
Direct Brevo API test - bypass Django to test pure API connectivity.
"""
import os
import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = os.getenv("BREVO_API_KEY", "")

if not API_KEY:
    print("ERROR: BREVO_API_KEY not set")
    exit(1)

print("=" * 70)
print("BREVO API TEST")
print("=" * 70)

headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}

# Test account
print("\n[1] Testing API Key...")
try:
    response = requests.get(
        "https://api.brevo.com/v3/account",
        headers=headers,
        timeout=10,
        verify=False
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK - Account: {data.get('email')}")
    else:
        print(f"ERROR {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"ERROR: {str(e)[:200]}")

# Test senders
print("\n[2] Fetching senders...")
try:
    response = requests.get(
        "https://api.brevo.com/v3/senders",
        headers=headers,
        timeout=10,
        verify=False
    )
    
    if response.status_code == 200:
        senders = response.json().get("senders", [])
        print(f"OK - Found {len(senders)} senders:")
        for s in senders:
            verified = "VERIFIED" if s.get("isVerified") else "NOT VERIFIED"
            print(f"  - {s.get('email')} [{verified}]")
    else:
        print(f"ERROR {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"ERROR: {str(e)[:200]}")

print("\n" + "=" * 70)
