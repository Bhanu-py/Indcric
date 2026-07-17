#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from apps.accounts.models import User

print("=" * 80)
print("ALL USERS IN DATABASE")
print("=" * 80)

for user in User.objects.all():
    print(f"\nID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"First Name: {user.first_name}")
    print(f"Last Name: {user.last_name}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Is Superuser: {user.is_superuser}")
    print(f"Is Active: {user.is_active}")
    print("-" * 80)

print("\n" + "=" * 80)
print("REGULAR USERS (Non-Staff, Non-Admin)")
print("=" * 80)

regular_users = User.objects.filter(is_staff=False, is_superuser=False)
for user in regular_users:
    print(f"✓ ID: {user.id}, Username: {user.username}, Email: {user.email}")

if not regular_users.exists():
    print("❌ No regular users found. Creating test user...")
    # Create a test user
    test_user = User.objects.create_user(
        username='regularuser',
        email='regular@test.com',
        password='testpass123',
        first_name='Regular',
        last_name='User'
    )
    print(f"✓ Created test user:")
    print(f"  Username: {test_user.username}")
    print(f"  Email: {test_user.email}")
    print(f"  Password: testpass123")
    print(f"  ID: {test_user.id}")
