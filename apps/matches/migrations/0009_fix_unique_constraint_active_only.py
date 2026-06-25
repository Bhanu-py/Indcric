# Migration to fix unique constraint - only enforce for active access
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matches", "0008_fix_temporaryscoringaccess_session_type"),
    ]

    operations = [
        # Remove the old unique_together constraint
        migrations.RemoveConstraint(
            model_name='temporaryscoringaccess',
            name='unique_user_session_access',
        ),
        # Add a new unique constraint that only applies when is_active=True
        migrations.AddConstraint(
            model_name='temporaryscoringaccess',
            constraint=models.UniqueConstraint(
                fields=['user', 'session'],
                condition=models.Q(is_active=True),
                name='unique_active_user_session_access',
            ),
        ),
    ]
