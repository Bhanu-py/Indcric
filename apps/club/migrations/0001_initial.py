import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ClubConsultationResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("connection", models.CharField(blank=True, max_length=160)),
                ("proceed_choice", models.CharField(choices=[("yes", "Yes, I agree that we should start the club."), ("no", "No, I do not think we should start the club at this time."), ("more_info", "I need more information before deciding.")], max_length=20)),
                ("membership_preference", models.CharField(choices=[("annual", "Annual membership"), ("monthly", "Monthly membership"), ("per_game", "Payment for each game or training session"), ("combined", "A combination of annual and occasional membership"), ("not_sure", "I am not sure yet")], max_length=20)),
                ("volunteering_choice", models.CharField(choices=[("yes", "Yes"), ("no", "No"), ("maybe", "Maybe, depending on the role and time required")], max_length=20)),
                ("responsibilities", models.JSONField(blank=True, default=list)),
                ("other_responsibility", models.CharField(blank=True, max_length=160)),
                ("time_commitment", models.CharField(blank=True, choices=[("weekly", "A few hours each week"), ("monthly", "A few hours each month"), ("specific_task", "Only when a specific task is assigned"), ("occasional", "Only occasionally"), ("not_sure", "I am not sure yet")], max_length=20)),
                ("comments", models.TextField(blank=True)),
                ("consent", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="club_consultation_responses", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "club consultation response",
                "verbose_name_plural": "club consultation responses",
                "ordering": ["-updated_at", "-id"],
            },
        ),
    ]
