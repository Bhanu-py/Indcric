# Generated migration for TemporaryScoringAccess model
# Date: 2026-06-24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sessions", "0001_initial"),
        ("matches", "0006_innings_single_batting"),
    ]

    operations = [
        migrations.CreateModel(
            name="TemporaryScoringAccess",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "granted_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "expires_at",
                    models.DateTimeField(),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True),
                ),
                (
                    "reason",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "granted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="granted_scoring_access",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="temporary_scoring_access",
                        to="sessions.session",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="temporary_scoring_access",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Temporary Scoring Access",
                "verbose_name_plural": "Temporary Scoring Access",
                "ordering": ["-granted_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="temporaryscoringaccess",
            constraint=models.UniqueConstraint(
                fields=("user", "session"),
                name="unique_user_session_access",
            ),
        ),
    ]
