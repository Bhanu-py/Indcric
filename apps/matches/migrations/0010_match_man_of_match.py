# Generated for Player-of-the-Match award (orange/purple cap + MoM).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matches", "0009_fix_unique_constraint_active_only"),
    ]

    operations = [
        migrations.AddField(
            model_name="match",
            name="man_of_match",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="matches.player",
            ),
        ),
    ]
