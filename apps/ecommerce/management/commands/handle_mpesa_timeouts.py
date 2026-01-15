from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.ecommerce.models import MPesaTransaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Handle timed out M-Pesa transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=10,
            help='Hours after which pending transactions are considered timed out (default: 10)'
        )

    def handle(self, *args, **options):
        timeout_hours = options['hours']
        cutoff_time = timezone.now() - timedelta(hours=timeout_hours)

        # Find pending transactions older than cutoff time
        timed_out_transactions = MPesaTransaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )

        processed_count = 0
        order_updates = 0
        sale_updates = 0

        self.stdout.write(
            self.style.WARNING(
                f"Processing {timed_out_transactions.count()} timed out M-Pesa transactions..."
            )
        )

        for transaction in timed_out_transactions:
            # Mark transaction as timed out
            transaction.status = 'timeout'
            transaction.error_message = f'Transaction timed out after {timeout_hours} hours'
            transaction.save()

            processed_count += 1

            # Update related records
            if transaction.order:
                # Update order payment status
                order = transaction.order
                if order.payment_status == 'pending':
                    order.payment_status = 'failed'
                    order.save()
                order_updates += 1
                logger.info(f"Updated order {order.order_number} due to M-Pesa timeout")

            elif transaction.pos_sale:
                # Update POS sale
                sale = transaction.pos_sale
                if sale.status == 'pending_payment':
                    sale.status = 'cancelled'
                    sale.save()

                    # Restore inventory
                    for item in sale.items.all():
                        if item.product.track_quantity:
                            item.product.quantity_in_stock += item.quantity
                            item.product.save()
                sale_updates += 1
                logger.info(f"Cancelled POS sale {sale.sale_number} due to M-Pesa timeout")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {processed_count} timed out transactions. "
                f"Orders: {order_updates}, Sales: {sale_updates}"
            )
        )
