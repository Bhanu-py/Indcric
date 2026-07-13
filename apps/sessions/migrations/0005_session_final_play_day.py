from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cric_sessions', '0004_session_date_option_1_session_date_option_2'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='final_play_day',
            field=models.CharField(blank=True, choices=[('sat', 'Saturday'), ('sun', 'Sunday'), ('both', 'Both days')], max_length=10, null=True),
        ),
    ]
