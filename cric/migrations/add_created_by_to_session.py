from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        # Make sure this matches your latest applied migration
        ('cric', '0001_initial'),
    ]

    operations = [
        # Column already created in 0001_initial — state-only to avoid duplicate column error
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='session',
                    name='created_by',
                    field=models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='created_sessions',
                        to='cric.user',
                    ),
                ),
            ],
        ),
    ]
