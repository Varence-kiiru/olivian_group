"""
Notification Service for sending SMS and email notifications
"""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests
import logging
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via SMS and email"""

    def __init__(self):
        self.sms_enabled = getattr(settings, 'SMS_ENABLED', False)
        self.sms_api_url = getattr(settings, 'SMS_API_URL', '')
        self.sms_api_key = getattr(settings, 'SMS_API_KEY', '')
        self.sms_sender_id = getattr(settings, 'SMS_SENDER_ID', 'OLIVIAN')

    def send_sms(self, phone_number, message):
        """
        Send SMS notification

        Args:
            phone_number (str): Recipient phone number
            message (str): SMS message content

        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        if not self.sms_enabled or not phone_number:
            logger.info(f"SMS not enabled or no phone number provided: {phone_number}")
            return False

        try:
            # Ensure phone number starts with country code
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]

            # TODO: Implement actual SMS gateway integration
            # This is a placeholder for the SMS API call

            # Example implementations for common SMS gateways:
            #
            # 1. Africa's Talking
            # response = requests.post(
            #     'https://api.africastalking.com/version1/messaging',
            #     headers={
            #         'apiKey': self.sms_api_key,
            #         'Content-Type': 'application/x-www-form-urlencoded',
            #         'Accept': 'application/json'
            #     },
            #     data={
            #         'username': getattr(settings, 'AFRICASTALKING_USERNAME', ''),
            #         'to': phone_number,
            #         'message': message,
            #         'from': self.sms_sender_id
            #     }
            # )
            #
            # 2. Twilio
            # from twilio.rest import Client
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # message = client.messages.create(
            #     body=message,
            #     from_=settings.TWILIO_PHONE_NUMBER,
            #     to=phone_number
            # )

            # For now, just log the SMS attempt
            logger.info(f"SMS sent to {phone_number}: {message[:50]}...")

            # Simulate success for development
            if getattr(settings, 'DEBUG', False):
                return True

            return True  # Placeholder return

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False

    def send_email(self, to_email, subject, template_name, context, from_email=None):
        """
        Send HTML email notification using Django templates

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            template_name (str): Template file name
            context (dict): Template context variables
            from_email (str): Optional sender email

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not to_email:
            logger.info("No email address provided")
            return False

        try:
            if from_email is None:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@olivian.co.ke')

            # Render HTML and text versions
            html_message = render_to_string(template_name, context)

            # Send email
            send_mail(
                subject=subject,
                message=html_message,  # Also used as text version for fallback
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_email_with_attachment(self, to_email, subject, template_name, context,
                                 from_email=None, attachment_path=None):
        """
        Send HTML email notification with optional PDF attachment

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            template_name (str): Template file name
            context (dict): Template context variables
            from_email (str): Optional sender email
            attachment_path (str): Optional path to PDF file to attach

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not to_email:
            logger.info("No email address provided")
            return False

        try:
            if from_email is None:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@olivian.co.ke')

            # Render HTML and text versions
            html_message = render_to_string(template_name, context)
            text_message = strip_tags(html_message)

            # Create email with attachment support
            from django.core.mail import EmailMultiAlternatives
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=[to_email] if isinstance(to_email, str) else to_email
            )
            email.attach_alternative(html_message, "text/html")

            # Attach file if provided
            if attachment_path:
                try:
                    with open(attachment_path, 'rb') as attachment_file:
                        content = attachment_file.read()
                        filename = attachment_path.split('/')[-1] if '/' in attachment_path else attachment_path.split('\\')[-1]
                        email.attach(filename, content, 'application/pdf')
                        logger.info(f"Attached PDF: {filename}")
                except Exception as attach_error:
                    logger.error(f"Failed to attach file {attachment_path}: {str(attach_error)}")
                    # Continue sending email without attachment

            # Send email
            email.send()
            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_bulk_sms(self, phone_numbers, message):
        """
        Send SMS to multiple recipients

        Args:
            phone_numbers (list): List of phone numbers
            message (str): SMS message content

        Returns:
            dict: Results with success/failure counts
        """
        results = {'successful': 0, 'failed': 0, 'errors': []}

        for phone in phone_numbers:
            if self.send_sms(phone, message):
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(phone)

        logger.info(f"Bulk SMS sent: {results['successful']} successful, {results['failed']} failed")
        return results

    def send_payment_notification(self, phone_number, amount, receipt_number, customer_name=None):
        """
        Send payment confirmation SMS

        Args:
            phone_number (str): Customer phone number
            amount (Decimal): Payment amount
            receipt_number (str): M-Pesa receipt number
            customer_name (str): Optional customer name

        Returns:
            bool: True if notification was sent successfully
        """
        if customer_name:
            message = (
                f"Dear {customer_name}, your payment of KES {amount:,.2f} "
                f"has been received. Receipt: {receipt_number}. "
                f"Thank you for choosing The Olivian Group!"
            )
        else:
            message = (
                f"Your payment of KES {amount:,.2f} has been received. "
                f"Receipt: {receipt_number}. Thank you for your business!"
            )

        return self.send_sms(phone_number, message)
