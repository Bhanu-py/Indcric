import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0010_match_man_of_match'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerMatchStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('runs', models.PositiveIntegerField(default=0)),
                ('balls_faced', models.PositiveIntegerField(default=0)),
                ('wickets', models.PositiveIntegerField(default=0)),
                ('balls_bowled', models.PositiveIntegerField(default=0)),
                ('runs_conceded', models.PositiveIntegerField(default=0)),
                ('catches', models.PositiveIntegerField(default=0)),
                ('runouts', models.PositiveIntegerField(default=0)),
                ('stumpings', models.PositiveIntegerField(default=0)),
                ('computed_at', models.DateTimeField(auto_now=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player_stats', to='matches.match')),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='player_match_stats', to='cric_sessions.session')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='match_stats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-session__date', '-match_id', 'user_id'],
                'unique_together': {('match', 'user')},
            },
        ),
    ]
