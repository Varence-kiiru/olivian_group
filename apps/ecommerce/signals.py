"""
Signal handlers for order email notifications
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from apps.core.email_utils import EmailService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def order_created_handler(sender, instance, created, **kwargs):
    """Send order confirmation email when a new order is created"""
    if created:
        try:
            # Send order confirmation email
            EmailService.send_order_confirmation_email(instance)
            logger.info(f"Order confirmation email sent for order {instance.order_number}")
            
            # If the order is set to pay_on_delivery, send that specific email too
            if instance.status == 'pay_on_delivery':
                EmailService.send_order_status_change_email(
                    order=instance,
                    previous_status='received',
                    new_status='pay_on_delivery',
                    notes='Order confirmed for pay on delivery'
                )
                logger.info(f"Pay on delivery email sent for order {instance.order_number}")
                
        except Exception as e:
            logger.error(f"Failed to send order confirmation email for {instance.order_number}: {e}")
