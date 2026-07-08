from django.core.management.base import BaseCommand

from apps.matches.models import Match
from apps.matches.rating_engine import (
    clear_match_ratings,
    completed_matches_queryset,
    compute_match_ratings,
    rebuild_all_ratings,
)


class Command(BaseCommand):
    help = "Rebuild player ratings from completed scored matches."

    def add_arguments(self, parser):
        parser.add_argument(
            '--match',
            type=int,
            default=None,
            help='Process one match ID instead of rebuilding every rating.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without writing changes.',
        )

    def handle(self, *args, **options):
        match_id = options['match']
        dry_run = options['dry_run']

        if match_id:
            match = Match.objects.filter(id=match_id).first()
            if not match:
                self.stderr.write(self.style.ERROR(f"Match {match_id} not found."))
                return
            if dry_run:
                action = "process" if match.is_completed else "clear stale ratings for"
                self.stdout.write(f"[dry-run] Would {action} match [{match.id}] {match.name}.")
                return
            updated = compute_match_ratings(match) if match.is_completed else clear_match_ratings(match)
            self.stdout.write(self.style.SUCCESS(
                f"Processed match [{match.id}] {match.name}; updated {updated} player(s)."
            ))
            return

        matches = list(completed_matches_queryset())
        if dry_run:
            self.stdout.write(f"Found {len(matches)} completed match(es).")
            for match in matches:
                label = f"[{match.id}] {match.name}"
                if match.session:
                    label = f"{label} ({match.session.name}, {match.session.date})"
                self.stdout.write(f"  [dry-run] Would process {label}")
            return

        processed_matches, affected_users = rebuild_all_ratings()
        self.stdout.write(self.style.SUCCESS(
            f"Done. Processed {processed_matches} completed match(es), updated {affected_users} player rating profile(s)."
        ))
