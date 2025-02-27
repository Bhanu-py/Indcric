# Generated by Django 5.1.6 on 2025-02-13 16:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("indcric", "0002_payment_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="match",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="indcric.match",
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="payment",
            unique_together={("user", "match")},
        ),
    ]
