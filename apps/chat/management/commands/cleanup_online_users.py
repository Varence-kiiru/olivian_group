from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.chat.models import UserActivity


class Command(BaseCommand):
    help = 'Clean up old online user activity records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Remove online users inactive for more than X days (default: 7)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)

        # Delete UserActivity records where last_activity is older than cutoff
        deleted_count, _ = UserActivity.objects.filter(
            last_activity__lt=cutoff_date,
            is_online=False
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {deleted_count} old online user records (older than {days} days)'
            )
        )

        # Show current online users count
        current_online = UserActivity.get_online_users().count()
        self.stdout.write(
            f'Currently {current_online} users are online'
        )
