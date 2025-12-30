"""
Management command to check for timeout on pending M-Pesa payments
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.ecommerce.models import MPesaTransaction, Order
from apps.pos.models import Sale


class Command(BaseCommand):
    help = 'Check and timeout pending M-Pesa transactions that exceed the timeout period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout-minutes',
            type=int,
            default=15,
            help='Timeout period in minutes for pending transactions (default: 15)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )

    def handle(self, *args, **options):
        timeout_minutes = options['timeout_minutes']
        dry_run = options['dry_run']
        timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)

        # Find pending transactions that have exceeded the timeout
        pending_transactions = MPesaTransaction.objects.filter(
            status='pending',
            created_at__lt=timeout_threshold
        )

        self.stdout.write(f"Found {pending_transactions.count()} pending transactions older than {timeout_minutes} minutes")

        if dry_run:
            for transaction in pending_transactions:
                self.stdout.write(f"Would timeout: Transaction {transaction.id} for {transaction.account_reference} (created: {transaction.created_at})")
            return

        # Process time-out transactions
        timeout_count = 0
        for transaction in pending_transactions:
            # Mark transaction as timed out
            transaction.status = 'failed'
            transaction.error_message = f'Payment timed out after {timeout_minutes} minutes'
            transaction.save()

            # Update related order or sale status
            if transaction.order:
                order = transaction.order
                if order.payment_status == 'pending':
                    order.payment_status = 'failed'
                    order.status = 'payment_timeout'
                    order.status_notes = f'M-Pesa payment timed out after {timeout_minutes} minutes'
                    order.save()
                    self.stdout.write(f"Order {order.order_number} marked as payment_timeout")

            elif transaction.pos_sale:
                sale = transaction.pos_sale
                if sale.status == 'pending_payment':
                    sale.status = 'payment_timeout'
                    sale.status_notes = f'M-Pesa payment timed out after {timeout_minutes} minutes'
                    sale.save()
                    self.stdout.write(f"Sale {sale.sale_number} marked as payment_timeout")

            timeout_count += 1

        if timeout_count > 0:
            self.stdout.write(f"Successfully processed {timeout_count} timed-out transactions")
        else:
            self.stdout.write("No transactions to process")
