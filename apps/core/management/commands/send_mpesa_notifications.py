from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.ecommerce.models import MPesaTransaction
from apps.core.services import NotificationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send SMS/email notifications for completed M-Pesa transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Check transactions from the last N days (default: 1)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)

        # Find completed transactions without notifications sent
        completed_transactions = MPesaTransaction.objects.filter(
            status='completed',
            mpesa_receipt_number__isnull=False,
            transaction_date__gte=cutoff_date,
            notification_sent=False  # Only send to transactions that haven't been notified
        ).select_related('order', 'pos_sale')

        self.stdout.write(
            self.style.WARNING(
                f"Processing {completed_transactions.count()} completed M-Pesa transactions..."
            )
        )

        notification_service = NotificationService()
        sent_count = 0
        failed_count = 0

        for transaction in completed_transactions:
            try:
                success = self._send_transaction_notification(
                    transaction, notification_service
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing transaction {transaction.id}: {str(e)}")
                )
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Notifications processed. Sent: {sent_count}, Failed: {failed_count}"
            )
        )

    def _send_transaction_notification(self, transaction, notification_service):
        """Send notification for a single transaction"""
        try:
            # Get customer contact info
            customer_phone = None
            customer_email = None
            customer_name = None

            # Try to get customer from order first
            if transaction.order and transaction.order.customer:
                customer = transaction.order.customer
                customer_phone = customer.phone
                customer_email = customer.email
                customer_name = customer.name

            # Fall back to POS sale customer
            elif transaction.pos_sale and transaction.pos_sale.customer:
                customer = transaction.pos_sale.customer
                customer_phone = customer.phone
                customer_email = customer.email
                customer_name = customer.name

            # If no customer found, use transaction phone
            if not customer_phone:
                customer_phone = transaction.phone_number
                customer_name = f"Customer ({customer_phone})"

            if not customer_phone:
                return False  # Can't send notification without phone

            # Format amount
            amount = f"{transaction.amount:,.2f}"

            # Prepare SMS message
            sms_message = (
                f"Dear {customer_name}, your payment of KES {amount} "
                f"has been received. Receipt: {transaction.mpesa_receipt_number}. "
                f"Thank you for choosing The Olivian Group!"
            )

            # Send SMS
            sms_success = notification_service.send_sms(customer_phone, sms_message)

            # Send email if available
            email_success = False
            if customer_email:
                email_subject = f"M-Pesa Payment Confirmation - Receipt {transaction.mpesa_receipt_number}"
                email_template = 'emails/mpesa_payment_confirmation.html'
                email_context = {
                    'customer_name': customer_name,
                    'amount': amount,
                    'receipt_number': transaction.mpesa_receipt_number,
                    'transaction_date': transaction.transaction_date,
                    'phone_number': customer_phone,
                }

                # Generate or get receipt PDF
                pdf_path = None
                if transaction.order:
                    try:
                        # Check if receipt exists and has PDF
                        if hasattr(transaction.order, 'receipt') and transaction.order.receipt and transaction.order.receipt.receipt_file:
                            pdf_path = transaction.order.receipt.receipt_file.path
                        else:
                            # Generate new receipt if needed
                            receipt = transaction.order.generate_receipt()
                            if receipt and receipt.receipt_file:
                                pdf_path = receipt.receipt_file.path
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"Could not generate receipt PDF for transaction {transaction.id}: {str(e)}")
                        )

                email_success = notification_service.send_email_with_attachment(
                    customer_email, email_subject, email_template, email_context, attachment_path=pdf_path
                )

            if sms_success or email_success:
                # Update notification tracking fields
                transaction.sms_sent = sms_success
                transaction.email_sent = email_success
                transaction.notification_sent = True
                transaction.notification_sent_at = timezone.now()
                transaction.save(update_fields=['sms_sent', 'email_sent', 'notification_sent', 'notification_sent_at'])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Notification sent for transaction {transaction.id} "
                        f"(SMS: {'✓' if sms_success else '✗'}, Email: {'✓' if email_success else '✗'})"
                    )
                )
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(f"Failed to send any notification for transaction {transaction.id}")
                )
                return False

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error sending notification for transaction {transaction.id}: {str(e)}")
            )
            return False
