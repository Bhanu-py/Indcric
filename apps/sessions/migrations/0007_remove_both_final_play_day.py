from django.db import migrations, models


def reset_both_final_play_day(apps, schema_editor):
    Session = apps.get_model('cric_sessions', 'Session')
    Session.objects.filter(final_play_day='both').update(final_play_day=None)


class Migration(migrations.Migration):

    dependencies = [
        ('cric_sessions', '0006_attendance_cost_exempt'),
    ]

    operations = [
        migrations.RunPython(reset_both_final_play_day, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='session',
            name='final_play_day',
            field=models.CharField(
                blank=True,
                choices=[('sat', 'Saturday'), ('sun', 'Sunday')],
                max_length=10,
                null=True,
            ),
        ),
    ]
