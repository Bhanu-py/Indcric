from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('cric', '0001_initial'),  # Make sure this matches your latest applied migration
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_sessions',
                to='cric.user',
            ),
        ),
    ]