from django.db import migrations


# Em-dashes look ugly on the support page; rewrite the General Donations seed
# copy + the fund-item descriptions that used them. Idempotent on re-run: only
# touches the default campaign and only updates rows whose text still matches
# the originals from migrations 0005/0006 (so an admin edit isn't clobbered).

GENERAL_BLURB_OLD = (
    "Support Indian Cricket Ghent — running costs, kit, drinks, hosting, "
    "and everything else that keeps the club going."
)
GENERAL_BLURB_NEW = (
    "Donations cover the running costs, kit, drinks, hosting, and everything "
    "else that keeps the club going."
)

# title -> (old description, new description)
FUND_ITEM_REWRITES = {
    'Always-on hosting': (
        'A paid server that never sleeps — no more cold-start lag.',
        'A paid server that never sleeps. No more cold-start lag.',
    ),
}


def rewrite(apps, schema_editor):
    DonationCampaign = apps.get_model('donations', 'DonationCampaign')
    default = DonationCampaign.objects.filter(is_default=True).first()
    if default is None:
        return

    if default.blurb == GENERAL_BLURB_OLD:
        default.blurb = GENERAL_BLURB_NEW
        default.save(update_fields=['blurb'])

    for item in default.fund_items.all():
        rewrite_pair = FUND_ITEM_REWRITES.get(item.title)
        if not rewrite_pair:
            continue
        old, new = rewrite_pair
        if item.description == old:
            item.description = new
            item.save(update_fields=['description'])


def reverse(apps, schema_editor):
    DonationCampaign = apps.get_model('donations', 'DonationCampaign')
    default = DonationCampaign.objects.filter(is_default=True).first()
    if default is None:
        return

    if default.blurb == GENERAL_BLURB_NEW:
        default.blurb = GENERAL_BLURB_OLD
        default.save(update_fields=['blurb'])

    for item in default.fund_items.all():
        rewrite_pair = FUND_ITEM_REWRITES.get(item.title)
        if not rewrite_pair:
            continue
        old, new = rewrite_pair
        if item.description == new:
            item.description = old
            item.save(update_fields=['description'])


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0006_default_campaign_fund_items'),
    ]

    operations = [
        migrations.RunPython(rewrite, reverse),
    ]
