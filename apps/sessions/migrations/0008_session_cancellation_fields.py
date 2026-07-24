from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cric_sessions', '0007_remove_both_final_play_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='is_cancelled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='session',
            name='cancelled_reason',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='session',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
