import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from apps.chat.models import ChatRoom, Message, MessageReaction, MessageReadStatus, UserActivity, NotificationPreference
import shutil


class Command(BaseCommand):
    help = 'Clear chat data and attachments from the database and file system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rooms',
            nargs='*',
            type=str,
            help='Specific room names to clear (default: all rooms)',
        )
        parser.add_argument(
            '--clear-attachments',
            action='store_true',
            help='Delete chat attachment files from storage',
        )
        parser.add_argument(
            '--clear-user-activity',
            action='store_true',
            help='Clear all user activity and online status data',
        )
        parser.add_argument(
            '--clear-preferences',
            action='store_true',
            help='Clear user notification preferences',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleared without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('CHAT SYSTEM CLEAR COMMAND')
        )
        self.stdout.write(
            self.style.WARNING('=' * 50)
        )

        # Check if we have specific rooms
        if options['rooms']:
            rooms = ChatRoom.objects.filter(name__in=options['rooms'])
            if not rooms.exists():
                raise CommandError(f"No rooms found with names: {', '.join(options['rooms'])}")
        else:
            rooms = ChatRoom.objects.all()

        # Calculate what would be affected
        total_messages = Message.objects.filter(room__in=rooms).count()
        total_reactions = MessageReaction.objects.filter(message__room__in=rooms).count()
        total_read_status = MessageReadStatus.objects.filter(message__room__in=rooms).count()
        messages_with_attachments = Message.objects.filter(
            room__in=rooms,
            file_attachment__isnull=False
        ).count()

        if options['clear_user_activity']:
            total_activities = UserActivity.objects.count()
        else:
            total_activities = 0

        if options['clear_preferences']:
            total_preferences = NotificationPreference.objects.count()
        else:
            total_preferences = 0

        # Show what will be cleared
        self.stdout.write(f"Rooms to process: {rooms.count()}")
        self.stdout.write(f"Messages to delete: {total_messages}")
        self.stdout.write(f"Reactions to delete: {total_reactions}")
        self.stdout.write(f"Read statuses to delete: {total_read_status}")
        if options['clear_attachments']:
            self.stdout.write(f"Messages with attachments: {messages_with_attachments}")
        if options['clear_user_activity']:
            self.stdout.write(f"User activities to clear: {total_activities}")
        if options['clear_preferences']:
            self.stdout.write(f"Notification preferences to clear: {total_preferences}")

        # Dry run check
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS('DRY RUN - No changes made.')
            )
            return

        # Confirmation unless forced
        if not options['force']:
            confirm = input('\nAre you sure you want to proceed? Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled.')
                return

        try:
            with transaction.atomic():
                # Delete messages and related data
                messages = Message.objects.filter(room__in=rooms)
                self.stdout.write('Deleting messages and related data...')

                # Delete reactions
                MessageReaction.objects.filter(message__in=messages).delete()
                self.stdout.write(f'  - Deleted {total_reactions} reactions')

                # Delete read statuses
                MessageReadStatus.objects.filter(message__in=messages).delete()
                self.stdout.write(f'  - Deleted {total_read_status} read statuses')

                # Handle attachments before deleting messages
                if options['clear_attachments']:
                    self.stdout.write('Deleting attachment files...')
                    attachment_dir = os.path.join(settings.MEDIA_ROOT, 'chat_attachments')
                    deleted_files = 0

                    for message in messages.filter(file_attachment__isnull=False):
                        if message.file_attachment:
                            file_path = os.path.join(settings.MEDIA_ROOT, str(message.file_attachment))
                            try:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    deleted_files += 1
                            except Exception as e:
                                self.stderr.write(f'Failed to delete {file_path}: {e}')

                    # Remove attachment directory if empty
                    if os.path.exists(attachment_dir) and not os.listdir(attachment_dir):
                        try:
                            os.rmdir(attachment_dir)
                        except Exception as e:
                            self.stderr.write(f'Could not remove empty attachment directory: {e}')

                    self.stdout.write(f'  - Deleted {deleted_files} attachment files')

                # Delete messages
                messages.delete()
                self.stdout.write(f'  - Deleted {total_messages} messages')

                # Clear user activity if requested
                if options['clear_user_activity']:
                    UserActivity.objects.all().delete()
                    self.stdout.write(f'  - Cleared all user activity data')

                # Clear preferences if requested
                if options['clear_preferences']:
                    NotificationPreference.objects.all().delete()
                    self.stdout.write(f'  - Cleared all notification preferences')

                # Log the operation
                self.stdout.write(
                    self.style.SUCCESS('\nOperation completed successfully!')
                )
                self.stdout.write(f'  - Processed {rooms.count()} rooms')
                self.stdout.write(f'  - Total items removed: {total_messages + total_reactions + total_read_status + total_activities + total_preferences}')

        except Exception as e:
            raise CommandError(f'Error during cleanup: {e}')

        # Final statistics
        self.stdout.write('\nFinal status:')
        self.stdout.write(f'  - Rooms remaining: {ChatRoom.objects.count()}')
        self.stdout.write(f'  - Messages remaining: {Message.objects.count()}')
        self.stdout.write(f'  - Reactions remaining: {MessageReaction.objects.count()}')
        self.stdout.write(f'  - Read statuses remaining: {MessageReadStatus.objects.count()}')
