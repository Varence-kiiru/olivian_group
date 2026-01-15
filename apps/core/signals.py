"""
Signal handlers for automated email and in-app notifications
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from apps.core.email_utils import EmailService
from apps.core.models import Notification
from apps.accounts.models import update_employee_id_on_role_change
import logging

logger = logging.getLogger(__name__)

# User Registration and Authentication Signals
@receiver(post_save, sender='accounts.User')
def send_welcome_email(sender, instance, created, **kwargs):
    """Send welcome email when new user is created"""
    if created and instance.email:
        # Staff roles that don't require email verification
        staff_roles = ['super_admin', 'manager', 'sales_manager', 'sales_person',
                      'project_manager', 'inventory_manager', 'cashier', 'technician']

        # Only send automatic welcome email for staff members or when specifically requested
        # Customers get welcome emails only after email verification
        if instance.role in staff_roles or getattr(instance, '_send_welcome_email', False):
            try:
                EmailService.send_welcome_email(instance)
            except Exception as e:
                logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")

# Quotation Signals
@receiver(post_save, sender='quotations.Quotation')
def handle_quotation_notifications(sender, instance, created, **kwargs):
    """Handle quotation email and in-app notifications"""
    try:
        if created:
            logger.info(f"New quotation created: {instance.quotation_number}")
            # Send email notification
            result = EmailService.send_quotation_created_email(instance)
            logger.info(f"Email result for new quotation {instance.quotation_number}: {result}")

            # Create in-app notification for relevant users
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                # Notify sales managers and admins about new quotations
                sales_users = User.objects.filter(role__in=['super_admin', 'manager', 'sales_manager'])
                for user in sales_users:
                    Notification.create_notification(
                        user=user,
                        title=f'New Quotation Created',
                        message=f'Quotation {instance.quotation_number} has been created for {instance.customer_name or "Customer"}.',
                        notification_type='info',
                        category='quotation',
                        link_url=f'/quotations/{instance.id}/',
                        link_text='View Quotation'
                    )
            except Exception as e:
                logger.error(f"Failed to create quotation notification: {str(e)}")

        else:
            # Check if status changed to sent
            if hasattr(instance, '_original_status') and instance._original_status != instance.status:
                logger.info(f"Quotation {instance.quotation_number} status changed from {instance._original_status} to {instance.status}")
                if instance.status == 'sent':
                    result = EmailService.send_quotation_created_email(instance)
                    logger.info(f"Email result for sent quotation {instance.quotation_number}: {result}")

                    # Create in-app notification for relevant users
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()

                        sales_users = User.objects.filter(role__in=['super_admin', 'manager', 'sales_manager'])
                        for user in sales_users:
                            Notification.create_notification(
                                user=user,
                                title=f'Quotation Sent',
                                message=f'Quotation {instance.quotation_number} has been sent to {instance.customer_name or "Customer"}.',
                                notification_type='success',
                                category='quotation',
                                link_url=f'/quotations/{instance.id}/',
                                link_text='View Quotation'
                            )
                    except Exception as e:
                        logger.error(f"Failed to create quotation sent notification: {str(e)}")

                elif instance.status in ['accepted', 'rejected', 'expired']:
                    # Send status update notification
                    result = EmailService.send_quotation_updated_email(instance)
                    logger.info(f"Update email result for quotation {instance.quotation_number}: {result}")

                    # Create in-app notification
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()

                        status_messages = {
                            'accepted': 'accepted',
                            'rejected': 'rejected',
                            'expired': 'expired'
                        }

                        sales_users = User.objects.filter(role__in=['super_admin', 'manager', 'sales_manager'])
                        for user in sales_users:
                            Notification.create_notification(
                                user=user,
                                title=f'Quotation {status_messages[instance.status].title()}',
                                message=f'Quotation {instance.quotation_number} has been {status_messages[instance.status]}.',
                                notification_type='warning' if instance.status == 'expired' else 'success',
                                category='quotation',
                                link_url=f'/quotations/{instance.id}/',
                                link_text='View Quotation'
                            )
                    except Exception as e:
                        logger.error(f"Failed to create status update notification: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to send quotation notification: {str(e)}")
        import traceback
        logger.error(f"Signal error traceback: {traceback.format_exc()}")

@receiver(pre_save, sender='quotations.Quotation')
def track_quotation_status_changes(sender, instance, **kwargs):
    """Track quotation status changes"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except sender.DoesNotExist:
            instance._original_status = None

# Order and Receipt Signals
@receiver(post_save, sender='ecommerce.Order')
def handle_order_notifications(sender, instance, created, **kwargs):
    """Handle order email and in-app notifications"""
    try:
        if created:
            # Order confirmation email is now handled by apps/ecommerce/signals.py to avoid duplicates

            # Create in-app notification for staff about new orders
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                # Notify sales and admin staff about new orders
                order_handlers = User.objects.filter(role__in=['super_admin', 'manager', 'cashier'])
                for user in order_handlers:
                    Notification.create_notification(
                        user=user,
                        title=f'New Order Received',
                        message=f'Order #{instance.order_number} has been placed by {instance.customer_name or "Customer"} for {instance.get_total_display()}.',
                        notification_type='info',
                        category='order',
                        link_url=f'/ecommerce/orders/{instance.id}/',
                        link_text='View Order'
                    )
            except Exception as e:
                logger.error(f"Failed to create order notification: {str(e)}")

        else:
            # Check for payment status changes
            if hasattr(instance, '_original_payment_status') and instance._original_payment_status != instance.payment_status:
                if instance.payment_status == 'paid':
                    # Generate and send receipt
                    receipt = instance.generate_receipt()
                    if receipt:
                        EmailService.send_receipt_email(receipt)

                    # Create in-app notification for payment completion
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()

                        finance_users = User.objects.filter(role__in=['super_admin', 'manager', 'finance_manager', 'cashier'])
                        for user in finance_users:
                            Notification.create_notification(
                                user=user,
                                title=f'Payment Completed',
                                message=f'Payment for Order #{instance.order_number} has been completed. Amount: {instance.get_total_display()}.',
                                notification_type='success',
                                category='order',
                                link_url=f'/ecommerce/orders/{instance.id}/',
                                link_text='View Order'
                            )
                    except Exception as e:
                        logger.error(f"Failed to create payment notification: {str(e)}")

            # Check for order status changes and send status change emails
            if hasattr(instance, '_original_status') and instance._original_status != instance.status:
                try:
                    EmailService.send_order_status_change_email(
                        order=instance,
                        previous_status=instance._original_status,
                        new_status=instance.status,
                        notes='Automatic status update from payment processing'
                    )
                    logger.info(f"Order status change email sent for order {instance.order_number}: {instance._original_status} → {instance.status}")
                except Exception as e:
                    logger.error(f"Failed to send order status change email for {instance.order_number}: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to send order notification: {str(e)}")

@receiver(pre_save, sender='ecommerce.Order')
def track_order_changes(sender, instance, **kwargs):
    """Track order changes"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_payment_status = original.payment_status
            instance._original_status = original.status
        except sender.DoesNotExist:
            instance._original_payment_status = None
            instance._original_status = None

@receiver(post_save, sender='ecommerce.Receipt')
def handle_receipt_notifications(sender, instance, created, **kwargs):
    """Handle receipt email notifications"""
    try:
        if created:
            EmailService.send_receipt_email(instance)
    except Exception as e:
        logger.error(f"Failed to send receipt notification: {str(e)}")

# Project Signals
@receiver(post_save, sender='projects.Project')
def handle_project_notifications(sender, instance, created, **kwargs):
    """Handle project email notifications"""
    try:
        # Only send automatic notifications for status changes, not creation
        # Creation notifications are handled in the views with user opt-in
        if not created:
            # Check for status changes
            if hasattr(instance, '_original_status') and instance._original_status != instance.status:
                EmailService.send_project_status_update_email(instance)
    except Exception as e:
        logger.error(f"Failed to send project notification: {str(e)}")

@receiver(pre_save, sender='projects.Project')
def track_project_changes(sender, instance, **kwargs):
    """Track project changes"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except sender.DoesNotExist:
            instance._original_status = None

# Budget and Payment Signals
@receiver(post_save, sender='budget.PaymentSchedule')
def handle_payment_reminders(sender, instance, created, **kwargs):
    """Handle payment reminder notifications"""
    try:
        if created and instance.send_reminder:
            EmailService.send_payment_reminder_email(instance)
    except Exception as e:
        logger.error(f"Failed to send payment reminder: {str(e)}")

# Inventory Signals
@receiver(post_save, sender='products.Product')
def handle_stock_alerts(sender, instance, created, **kwargs):
    """Handle low stock alerts"""
    try:
        if not created:  # Only for updates
            if hasattr(instance, 'quantity_available') and hasattr(instance, 'minimum_stock_level'):
                if instance.quantity_available <= instance.minimum_stock_level:
                    # Send email alert
                    EmailService.send_low_stock_alert(instance)

                    # Create in-app notification for inventory managers
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()

                        inventory_managers = User.objects.filter(role__in=['super_admin', 'manager', 'inventory_manager'])
                        for user in inventory_managers:
                            Notification.create_notification(
                                user=user,
                                title=f'Low Stock Alert',
                                message=f'Product "{instance.name}" is running low. Current stock: {instance.quantity_available}, Minimum level: {instance.minimum_stock_level}.',
                                notification_type='warning',
                                category='inventory',
                                link_url=f'/products/manage/',
                                link_text='View Products'
                            )
                    except Exception as e:
                        logger.error(f"Failed to create low stock notification: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to send stock alert: {str(e)}")


# Employee ID Management Signals
@receiver(pre_save, sender='accounts.User')
def track_user_role_changes(sender, instance, **kwargs):
    """Track user role changes for employee ID management"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_role = original.role
            instance._original_employee_id = original.employee_id
        except sender.DoesNotExist:
            instance._original_role = None
            instance._original_employee_id = None

@receiver(post_save, sender='accounts.User')
def handle_employee_id_assignment(sender, instance, created, **kwargs):
    """Automatically assign/change Employee ID when role changes"""
    try:
        needs_save = False

        # Handle role changes - Check if role actually changed from customer/other to staff
        if hasattr(instance, '_original_role') and instance._original_role != instance.role:
            # Role changed - only assign ID if new role is staff
            if instance.role in ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person', 'project_manager', 'inventory_manager', 'cashier', 'technician']:
                update_employee_id_on_role_change(instance, instance.role)
                needs_save = True
                logger.info(f"Employee ID updated for {instance.username} due to role change from {instance._original_role} to {instance.role}")
            elif instance._original_role in ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person', 'project_manager', 'inventory_manager', 'cashier', 'technician']:
                # Role changed from staff to non-staff - could clear employee ID if desired
                logger.info(f"User {instance.username} role changed from staff to {instance.role} - employee ID preserved")

        # Handle new staff creation or existing staff without employee ID
        if not created and not instance.employee_id and instance.role in ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person', 'project_manager', 'inventory_manager', 'cashier', 'technician']:
            update_employee_id_on_role_change(instance, instance.role)
            needs_save = True
            logger.info(f"Employee ID assigned for existing user {instance.username} with role {instance.role}")

        # Handle new staff user creation
        if created and instance.role in ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person', 'project_manager', 'inventory_manager', 'cashier', 'technician'] and not instance.employee_id:
            update_employee_id_on_role_change(instance, instance.role)
            needs_save = True
            logger.info(f"Employee ID assigned for new user {instance.username}")

        # Save if we updated the employee_id
        if needs_save and instance.employee_id:
            # Use update_fields to avoid infinite loop
            instance.save(update_fields=['employee_id'])

    except Exception as e:
        logger.error(f"Failed to handle employee ID assignment for {instance.username}: {str(e)}")
