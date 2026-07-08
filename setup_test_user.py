#!/usr/bin/env python
"""
Setup script to create a test staff user for local testing
Run with: python manage.py shell < setup_test_user.py
"""

from django.contrib.auth.models import User

# Check if test user already exists
username = 'testadmin'
email = 'testadmin@local.test'

try:
    user = User.objects.get(username=username)
    print(f"✅ User '{username}' already exists")
    print(f"   Email: {user.email}")
    print(f"   Is Staff: {user.is_staff}")
except User.DoesNotExist:
    # Create new staff user
    user = User.objects.create_user(
        username=username,
        email=email,
        password='testpass123',
        is_staff=True,
        is_superuser=False
    )
    print(f"✅ Created new test staff user!")
    print(f"   Username: {username}")
    print(f"   Password: testpass123")
    print(f"   Email: {email}")

# Ensure the user is staff
if not user.is_staff:
    user.is_staff = True
    user.save()
    print(f"✅ Made '{username}' a staff member")

print(f"\n📋 Login credentials for testing:")
print(f"   URL: http://127.0.0.1:8000/accounts/login/")
print(f"   Username: {username}")
print(f"   Password: testpass123")
print(f"\n🎯 Then go to: http://127.0.0.1:8000/accounts/manage/manage-users/")
