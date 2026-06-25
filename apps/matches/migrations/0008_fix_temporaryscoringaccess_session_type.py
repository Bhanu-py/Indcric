# Migration to fix the session foreign key type
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("matches", "0007_temporaryscoringaccess"),
    ]

    operations = [
        # Drop the problematic foreign key constraint
        migrations.RemoveConstraint(
            model_name='temporaryscoringaccess',
            name='unique_user_session_access',
        ),
        # Delete the old table and recreate it with correct schema
        migrations.DeleteModel(
            name='TemporaryScoringAccess',
        ),
        # Recreate with explicit ForeignKey to cric_sessions.Session
        migrations.CreateModel(
            name='TemporaryScoringAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('reason', models.TextField(blank=True, default='')),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_scoring_access', to='accounts.user')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temporary_scoring_access', to='cric_sessions.session')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temporary_scoring_access', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Temporary Scoring Access',
                'verbose_name_plural': 'Temporary Scoring Access',
                'ordering': ['-granted_at'],
            },
        ),
        # Re-add the unique constraint
        migrations.AddConstraint(
            model_name='temporaryscoringaccess',
            constraint=models.UniqueConstraint(fields=('user', 'session'), name='unique_user_session_access'),
        ),
    ]
