"""Set drink preferences for all players on the live DB.
Run after setting the DB connection string env var.
"""
from django.contrib.auth import get_user_model
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

User = get_user_model()

ALCOHOL_IDS = [
    35, 16, 50, 39, 21, 40, 54, 41, 37, 58,
    28, 57, 56, 33, 42, 22, 43, 48, 45, 55,
    31, 1, 46, 14, 34, 60, 20,
]

NON_ALCOHOL_IDS = [
    15, 32, 38, 36, 59, 29, 30, 47, 44, 49,
    51, 52, 53,
]

a = User.objects.filter(id__in=ALCOHOL_IDS).update(drink_preference='alcohol')
n = User.objects.filter(id__in=NON_ALCOHOL_IDS).update(
    drink_preference='non_alcohol')

print(f"Set {a} players → alcohol")
print(f"Set {n} players → non_alcohol")
print("Done.")
