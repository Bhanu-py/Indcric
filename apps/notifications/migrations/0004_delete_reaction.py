from django.db import migrations


class Migration(migrations.Migration):
    """Drop the activity-feed Reaction table — the tap-to-react feature was
    removed from the UI."""

    dependencies = [
        ('notifications', '0003_activityevent_dedup_key_and_more'),
    ]

    operations = [
        migrations.DeleteModel(name='Reaction'),
    ]
