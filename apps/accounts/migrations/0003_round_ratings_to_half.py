from decimal import Decimal

from django.db import migrations


def _round_to_half(value):
    if value is None:
        return None
    return Decimal(str(round(float(value) * 2) / 2))


def round_existing_ratings(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    fields = ('batting_rating', 'bowling_rating', 'fielding_rating')
    for user in User.objects.all():
        changed = []
        for f in fields:
            current = getattr(user, f)
            rounded = _round_to_half(current)
            if current != rounded:
                setattr(user, f, rounded)
                changed.append(f)
        if changed:
            user.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(round_existing_ratings, reverse_code=migrations.RunPython.noop),
    ]
