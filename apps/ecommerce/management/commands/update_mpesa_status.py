from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.ecommerce.models import MPesaTransaction
from apps.ecommerce.mpesa import MPesaSTKPush
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update status of pending M-Pesa transactions by querying Safaricom API'

    def handle(self, *args, **options):
        # Find pending transactions that started within the last 48 hours
        # (M-Pesa query might not work beyond that timeframe)
        cutoff_time = timezone.now() - timedelta(hours=48)

        pending_transactions = MPesaTransaction.objects.filter(
            status='pending',
            created_at__gte=cutoff_time,
            checkout_request_id__isnull=False
        )

        self.stdout.write(
            self.style.WARNING(
                f"Checking status for {pending_transactions.count()} pending M-Pesa transactions..."
            )
        )

        updated_count = 0
        completed_count = 0
        failed_count = 0

        for transaction in pending_transactions:
            try:
                # Query transaction status from M-Pesa
                mpesa = MPesaSTKPush()
                status_response = mpesa.query_stk_status(transaction.checkout_request_id)

                if status_response.get('success'):
                    self.stdout.write(f"Transaction {transaction.id}: Got status response")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Transaction {transaction.id}: Failed to get status")
                    )
                    continue

                # Parse the response and update transaction
                result_code = status_response.get('ResultCode')
                result_desc = status_response.get('ResultDesc', '')

                if result_code == 0:  # Success
                    # Transaction completed
                    receipt_number = None
                    callback_metadata = status_response.get('CallbackMetadata', {}).get('Item', [])

                    for item in callback_metadata:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            receipt_number = item.get('Value')
                            break

                    if receipt_number:
                        # Update transaction as completed
                        transaction.status = 'completed'
                        transaction.mpesa_receipt_number = receipt_number
                        transaction.transaction_date = timezone.now()
                        transaction.save()
                        completed_count += 1

                        # Update related order or sale
                        self._update_related_records(transaction)

                        self.stdout.write(
                            self.style.SUCCESS(f"Transaction {transaction.id}: Completed with receipt {receipt_number}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Transaction {transaction.id}: Missing receipt number")
                        )

                elif result_code in [1, 1032, 1037]:  # Completed but not paid
                    # Transaction failed
                    transaction.status = 'failed'
                    transaction.error_message = result_desc or 'Payment failed'
                    transaction.save()
                    failed_count += 1

                    self.stdout.write(
                        self.style.ERROR(f"Transaction {transaction.id}: Failed - {result_desc}")
                    )

                else:
                    # Still processing or unknown status
                    self.stdout.write(f"Transaction {transaction.id}: Still processing (code: {result_code})")

                # Store the query response
                transaction.callback_response.update({
                    'status_query': status_response,
                    'status_query_time': timezone.now().isoformat()
                })
                transaction.save()

                updated_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error checking transaction {transaction.id}: {str(e)}")
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Status check complete. Updated: {updated_count}, "
                f"Completed: {completed_count}, Failed: {failed_count}"
            )
        )

    def _update_related_records(self, transaction):
        """Update related order or POS sale records"""
        from apps.ecommerce.models import Payment

        try:
            if transaction.order:
                # Update order
                order = transaction.order
                if order.payment_status == 'pending':
                    order.payment_status = 'paid'
                    order.mpesa_transaction_id = transaction.mpesa_receipt_number
                    order.save()

                    # Create or update payment record
                    payment, created = Payment.objects.get_or_create(
                        order=order,
                        payment_method='mpesa',
                        defaults={
                            'amount': transaction.amount,
                            'reference_number': transaction.mpesa_receipt_number,
                            'mpesa_receipt_number': transaction.mpesa_receipt_number,
                            'mpesa_phone_number': transaction.phone_number,
                            'transaction_date': transaction.transaction_date,
                            'status': 'completed'
                        }
                    )

                    if not created and payment.status != 'completed':
                        payment.status = 'completed'
                        payment.mpesa_receipt_number = transaction.mpesa_receipt_number
                        payment.transaction_date = transaction.transaction_date
                        payment.save()

                logger.info(f"Updated order {order.order_number} with M-Pesa payment")

            elif transaction.pos_sale:
                # Update POS sale
                sale = transaction.pos_sale
                if sale.status == 'pending_payment':
                    sale.status = 'completed'
                    sale.mpesa_transaction_id = transaction.mpesa_receipt_number
                    sale.save()

                    # Create or update POS payment record
                    from apps.pos.models import Payment as POSPayment
                    payment, created = POSPayment.objects.get_or_create(
                        sale=sale,
                        payment_type='mpesa',
                        defaults={
                            'amount': transaction.amount,
                            'transaction_id': transaction.mpesa_receipt_number,
                            'mpesa_receipt_number': transaction.mpesa_receipt_number,
                            'mpesa_phone_number': transaction.phone_number,
                            'status': 'completed'
                        }
                    )

                    if not created and payment.status != 'completed':
                        payment.status = 'completed'
                        payment.mpesa_receipt_number = transaction.mpesa_receipt_number
                        payment.save()

                logger.info(f"Completed POS sale {sale.sale_number} with M-Pesa payment")

        except Exception as e:
            logger.error(f"Error updating related records for transaction {transaction.id}: {str(e)}")
