from django.db import migrations, models


def forwards(apps, schema_editor):
    Vote = apps.get_model('polls', 'Vote')
    two_day_votes = Vote.objects.filter(
        poll__session__date_option_1__isnull=False,
        poll__session__date_option_2__isnull=False,
    )
    two_day_votes.filter(choice='yes').update(choice='sat')
    two_day_votes.filter(choice='no').update(choice='sun')


def backwards(apps, schema_editor):
    Vote = apps.get_model('polls', 'Vote')
    two_day_votes = Vote.objects.filter(
        poll__session__date_option_1__isnull=False,
        poll__session__date_option_2__isnull=False,
    )
    two_day_votes.filter(choice='sat').update(choice='yes')
    two_day_votes.filter(choice='sun').update(choice='no')


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0003_alter_vote_choice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='choice',
            field=models.CharField(
                choices=[
                    ('yes', 'Yes'),
                    ('no', 'No'),
                    ('sat', 'Saturday'),
                    ('sun', 'Sunday'),
                    ('all', 'Both'),
                    ('out', 'Not available'),
                ],
                max_length=3,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
