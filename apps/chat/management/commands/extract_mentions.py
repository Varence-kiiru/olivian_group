from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.chat.models import Message, ChatRoom

User = get_user_model()

class Command(BaseCommand):
    help = 'Extract @mentions from existing messages and populate the mentioned_users field'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of messages to process per batch',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        self.stdout.write(self.style.SUCCESS(f'Starting mention extraction ({"dry run" if dry_run else "live update"})'))

        # Get all messages
        messages = Message.objects.select_related('author').prefetch_related('mentioned_users')
        total_messages = messages.count()

        self.stdout.write(f'Processing {total_messages} messages...')

        processed = 0
        updated = 0

        for i in range(0, total_messages, batch_size):
            batch = messages[i:i+batch_size]

            for message in batch:
                mentioned_users = self.extract_mentions(message.content)
                current_mentions = set(message.mentioned_users.values_list('username', flat=True))

                if mentioned_users != current_mentions:
                    if not dry_run:
                        # Clear existing mentions and add new ones
                        message.mentioned_users.clear()
                        for username in mentioned_users:
                            try:
                                user = User.objects.get(username=username)
                                message.mentioned_users.add(user)
                                updated += 1
                            except User.DoesNotExist:
                                continue  # Skip non-existent users
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Would update message {message.id} with mentions: {sorted(mentioned_users)}'
                            )
                        )
                        updated += 1

                processed += 1

                if processed % 1000 == 0:
                    self.stdout.write(f'Processed {processed}/{total_messages} messages...')

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {updated} messages with mention information'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Would update {updated} messages with mention information (dry run)'
                )
            )

    def extract_mentions(self, content):
        """Extract @usernames from message content"""
        if not content:
            return set()

        import re
        # Match @ followed by word characters (letters, digits, underscore)
        # This matches patterns like @john, @user123, @john_doe
        mentions = re.findall(r'@(\w+)', content)
        return set(mentions)  # Return unique usernames
