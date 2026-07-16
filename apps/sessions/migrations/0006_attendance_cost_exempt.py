from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cric_sessions', '0005_session_final_play_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='cost_exempt',
            field=models.BooleanField(default=False),
        ),
    ]
