from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_alter_vote_choice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='choice',
            field=models.CharField(
                choices=[
                    ('yes', 'Saturday'),
                    ('no', 'Sunday'),
                    ('all', 'Both'),
                    ('out', 'Not available'),
                ],
                max_length=3,
            ),
        ),
    ]
