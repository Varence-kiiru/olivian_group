from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.quotations.models import QuotationFollowUp
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send reminders for upcoming follow-ups'

    def handle(self, *args, **options):
        # Get follow-ups scheduled in the next hour
        upcoming = QuotationFollowUp.objects.filter(
            scheduled_date__gte=timezone.now(),
            scheduled_date__lte=timezone.now() + timedelta(hours=1),
            completed=False
        )

        for follow_up in upcoming:
            follow_up.send_reminder_email()
            self.stdout.write(f"Sent reminder for follow-up {follow_up.id}")