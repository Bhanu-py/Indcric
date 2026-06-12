from django.db import migrations


# Drinks & gear feel more concrete / immediate than server hosting, so the
# user wants them at the top of the General Donations card. Reorder by title
# on the default campaign only — admin-created items on specific drives are
# left alone.

DESIRED_ORDER = [
    'Drinks & snacks',
    'Balls, bats & gear',
    'Always-on hosting',
    'A bigger database',
]


def reorder(apps, schema_editor):
    DonationCampaign = apps.get_model('donations', 'DonationCampaign')
    default = DonationCampaign.objects.filter(is_default=True).first()
    if default is None:
        return
    for index, title in enumerate(DESIRED_ORDER, start=1):
        default.fund_items.filter(title=title).update(order=index)


def reverse_reorder(apps, schema_editor):
    """Restore the original (server-first) order from migration 0006."""
    DonationCampaign = apps.get_model('donations', 'DonationCampaign')
    default = DonationCampaign.objects.filter(is_default=True).first()
    if default is None:
        return
    original = [
        'Always-on hosting',
        'A bigger database',
        'Drinks & snacks',
        'Balls, bats & gear',
    ]
    for index, title in enumerate(original, start=1):
        default.fund_items.filter(title=title).update(order=index)


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0007_rewrite_general_donations_copy'),
    ]

    operations = [
        migrations.RunPython(reorder, reverse_reorder),
    ]
