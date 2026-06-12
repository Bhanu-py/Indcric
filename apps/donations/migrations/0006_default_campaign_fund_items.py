from django.db import migrations


DEFAULT_FUND_ITEMS = [
    {
        'title': 'Always-on hosting',
        'description': 'A paid server that never sleeps — no more cold-start lag.',
        'icon': 'server',
        'color': 'pitch',
        'order': 1,
    },
    {
        'title': 'A bigger database',
        'description': 'More than the current 0.5 GB, with room to grow.',
        'icon': 'db',
        'color': 'sky',
        'order': 2,
    },
    {
        'title': 'Drinks & snacks',
        'description': 'Beers, water and bites for match days.',
        'icon': 'cup',
        'color': 'amber',
        'order': 3,
    },
    {
        'title': 'Balls, bats & gear',
        'description': 'Replacing kit as it wears out through the season.',
        'icon': 'ball',
        'color': 'emerald',
        'order': 4,
    },
]


def seed_default_fund_items(apps, schema_editor):
    """Move the support page's hardcoded 'what your donations fund' tiles onto
    the General Donations campaign as real FundItem rows. Lets us drop the
    duplicated block from the template and lets admins edit the items per
    campaign in the future (per-fundraiser breakdowns).

    Idempotent — skips when the default already has fund_items defined."""
    DonationCampaign = apps.get_model('donations', 'DonationCampaign')
    FundItem = apps.get_model('donations', 'FundItem')

    default = DonationCampaign.objects.filter(is_default=True).first()
    if default is None:
        return
    if default.fund_items.exists():
        return
    for item in DEFAULT_FUND_ITEMS:
        FundItem.objects.create(campaign=default, **item)


def unseed_default_fund_items(apps, schema_editor):
    DonationCampaign = apps.get_model('donations', 'DonationCampaign')
    default = DonationCampaign.objects.filter(is_default=True).first()
    if default is not None:
        default.fund_items.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0005_donationcampaign_is_default_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_default_fund_items, unseed_default_fund_items),
    ]
