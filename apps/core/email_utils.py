"""
Email utilities for Olivian Group system
Handles all email notifications for user interactions
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from apps.core.models import CompanySettings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Centralized email service for all system notifications"""
    
    # Company email addresses
    EMAILS = {
        'noreply': 'noreply@olivian.co.ke',
        'info': 'info@olivian.co.ke',
        'sales': 'sales@olivian.co.ke',
        'admin': 'admin@olivian.co.ke',
    }
    
    @classmethod
    def get_company_context(cls):
        """Get company settings for email templates"""
        try:
            company = CompanySettings.objects.first()
            # Build absolute logo URL for emails
            logo_url = None
            if company and company.logo:
                site_url = getattr(settings, 'SITE_URL', 'https://olivian.co.ke').rstrip('/')
                media_url = getattr(settings, 'MEDIA_URL', '/media/').strip('/')
                logo_url = f"{site_url}/{media_url}/{company.logo.name}"

            context = {
                'company_name': company.name if company else 'The Olivian Group Limited',
                'company_email': company.email if company else cls.EMAILS['info'],
                'company_phone': company.phone if company else '+254-719-728-666',
                'company_website': company.website if company else 'https://olivian.co.ke',
                'company_address': company.address if company else '',
                'primary_color': company.primary_color if company else '#38b6ff',
                'company': company,  # Include full company object for backward compatibility
                'logo_url': logo_url,  # Absolute URL for email templates
            }
            return context
        except Exception as e:
            logger.error(f"Error getting company context: {str(e)}")
            return {
                'company_name': 'The Olivian Group Limited',
                'company_email': cls.EMAILS['info'],
                'company_phone': '+254-719-728-666',
                'company_website': 'https://olivian.co.ke',
                'company_address': '',
                'primary_color': '#38b6ff',
                'company': None,  # Include company object even when None for template safety
                'logo_url': None,
            }
    
    @classmethod
    def send_email_notification(cls, template_name, context, recipient_email, 
                              subject, from_email=None):
        """Send HTML email notification"""
        try:
            if not from_email:
                from_email = cls.EMAILS['noreply']
            
            # Add company context
            context.update(cls.get_company_context())
            
            # Debug output
            logger.info(f"Sending email: template={template_name}, context keys={list(context.keys())}")
            
            # Render email templates
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Debug: log email content length
            logger.info(f"Email content length: HTML={len(html_content)}, Text={len(text_content)}")
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email] if isinstance(recipient_email, str) else recipient_email
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            import traceback
            logger.error(f"Email error traceback: {traceback.format_exc()}")
            return False
    
    @classmethod
    def send_email_with_pdf_attachment(cls, template_name, context, recipient_email,
                                     subject, from_email=None, quotation=None, file_path=None):
        """Send HTML email notification with PDF attachment"""
        try:
            if not from_email:
                from_email = cls.EMAILS['noreply']

            # Add company context
            context.update(cls.get_company_context())

            # Render email templates
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email] if isinstance(recipient_email, str) else recipient_email
            )
            email.attach_alternative(html_content, "text/html")

            # Attach PDF - check for file_path first, then quotation
            attachment_added = False
            if file_path:
                try:
                    # Read the file and attach it
                    with open(file_path, 'rb') as pdf_file:
                        pdf_content = pdf_file.read()

                    logger.info(f"PDF loaded from file {file_path}, content size: {len(pdf_content)} bytes")

                    # Extract filename from path
                    filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]

                    # Attach PDF
                    email.attach(
                        filename,
                        pdf_content,
                        'application/pdf'
                    )
                    logger.info(f"PDF attached to email: {filename}")
                    attachment_added = True

                except Exception as pdf_error:
                    logger.error(f"Failed to attach PDF from file {file_path}: {str(pdf_error)}")
                    import traceback
                    logger.error(f"PDF attachment traceback: {traceback.format_exc()}")
                    # Continue sending email without PDF attachment

            elif quotation:
                try:
                    logger.info(f"Starting PDF generation for quotation {quotation.quotation_number}")
                    from apps.quotations.views import QuotationPDFView
                    pdf_view = QuotationPDFView()
                    pdf_content = pdf_view.generate_quotation_pdf(quotation, return_response=False)

                    logger.info(f"PDF generated successfully, content size: {len(pdf_content)} bytes")

                    # Attach PDF
                    email.attach(
                        f'Quotation-{quotation.quotation_number}.pdf',
                        pdf_content,
                        'application/pdf'
                    )
                    logger.info(f"PDF attached to email for quotation {quotation.quotation_number}")
                    attachment_added = True

                except Exception as pdf_error:
                    logger.error(f"Failed to attach PDF for quotation {quotation.quotation_number}: {str(pdf_error)}")
                    import traceback
                    logger.error(f"PDF generation traceback: {traceback.format_exc()}")
                    # Continue sending email without PDF attachment

            # Send email
            email.send()
            logger.info(f"Email with attachment sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email with attachment to {recipient_email}: {str(e)}")
            return False
    
    # User Registration & Authentication
    @classmethod
    def send_email_verification(cls, user, verification_url):
        """Send email verification link to new users"""
        context = {
            'user_name': user.first_name or user.username,
            'user_email': user.email,
            'verification_url': verification_url,
        }
        return cls.send_email_notification(
            'email_verification',
            context,
            user.email,
            f'Verify your email address - {cls.get_company_context()["company_name"]}'
        )
    
    @classmethod
    def send_password_reset_email(cls, user, reset_url):
        """Send password reset link to users"""
        context = {
            'user_name': user.first_name or user.username,
            'user_email': user.email,
            'reset_url': reset_url,
        }
        return cls.send_email_notification(
            'password_reset',
            context,
            user.email,
            f'Reset your password - {cls.get_company_context()["company_name"]}'
        )
    
    @classmethod
    def send_welcome_email(cls, user):
        """Send welcome email to new users"""
        # Determine if user is staff or customer
        staff_roles = ['super_admin', 'manager', 'sales_manager', 'sales_person', 
                      'project_manager', 'inventory_manager', 'cashier', 'technician']
        
        if user.role in staff_roles:
            # Send staff welcome email
            context = {
                'user_name': user.first_name or user.username,
                'username': user.username,
                'user_email': user.email,
                'role': user.get_role_display(),
                'temporary_password': getattr(user, '_temp_password', 'Contact admin for password'),
                'employee_id': getattr(user, 'employee_id', None),
                'department': getattr(user, 'department', None),
                'login_url': f"{cls.get_company_context()['company_website']}/accounts/login/",
            }
            template_name = 'staff_welcome'
            subject = f'Welcome to the {cls.get_company_context()["company_name"]} Team!'
        else:
            # Send customer welcome email
            context = {
                'user_name': user.first_name or user.username,
                'user_email': user.email,
                'role': user.get_role_display(),
            }
            template_name = 'welcome'
            subject = 'Welcome to Olivian Group Solutions!'
        
        return cls.send_email_notification(
            template_name,
            context,
            user.email,
            subject
        )
    
    @classmethod
    def send_password_reset_email(cls, user, reset_link):
        """Send password reset email"""
        context = {
            'user_name': user.first_name or user.username,
            'reset_link': reset_link,
        }
        return cls.send_email_notification(
            'password_reset',
            context,
            user.email,
            'Reset Your Olivian Group Account Password'
        )
    
    # Quotation Notifications
    @classmethod
    def send_quotation_created_email(cls, quotation):
        """Notify customer when quotation is created with PDF attachment"""
        context = {
            'quotation': quotation,
            'customer_name': quotation.customer.name,
            'quotation_number': quotation.quotation_number,
            'total_amount': quotation.total_amount,
            'quotation_view_url': f"https://olivian.co.ke/quotations/view/{quotation.quotation_number}/",
        }
        return cls.send_email_with_pdf_attachment(
            'quotation_created',
            context,
            quotation.customer.email,
            f'Solar Quotation #{quotation.quotation_number} - Olivian Group',
            cls.EMAILS['sales'],
            quotation
        )
    
    @classmethod
    def send_quotation_updated_email(cls, quotation):
        """Notify customer when quotation is updated"""
        context = {
            'quotation': quotation,
            'customer_name': quotation.customer.name,
            'quotation_number': quotation.quotation_number,
        }
        return cls.send_email_notification(
            'quotation_updated',
            context,
            quotation.customer.email,
            f'Updated Quotation #{quotation.quotation_number} - Olivian Group',
            cls.EMAILS['sales']
        )
    
    # Order & Receipt Notifications
    @classmethod
    def send_order_confirmation_email(cls, order):
        """Send order confirmation to customer"""
        context = {
            'order': order,
            'customer_name': order.customer.name,
            'order_number': order.order_number,
            'total_amount': order.total_amount,
            'items': order.items.all(),
            'order_tracking_url': f"https://olivian.co.ke/track/{order.order_number}/",
        }
        return cls.send_email_notification(
            'order_confirmation',
            context,
            order.customer.email,
            f'Order Confirmation #{order.order_number} - Olivian Group',
            cls.EMAILS['sales']
        )
    
    @classmethod
    def send_receipt_email(cls, receipt):
        """Send receipt via email with PDF attachment"""
        context = {
            'receipt': receipt,
            'order': receipt.order,
            'customer_name': receipt.order.customer.name,
        }

        # Ensure PDF is generated
        if not receipt.receipt_file:
            receipt.generate_receipt_pdf()

        # Send email with PDF attachment
        email = cls.send_email_with_pdf_attachment(
            'receipt',
            context,
            receipt.order.customer.email,
            f'Receipt #{receipt.receipt_number} - Olivian Group',
            cls.EMAILS['sales'],
            None,  # No quotation, but method expects parameter
            receipt.receipt_file.path if receipt.receipt_file else None
        )

        # Update receipt email tracking
        if email:
            receipt.customer_email_sent = True
            receipt.customer_email_date = timezone.now()
            receipt.save()

        return email
    
    @classmethod
    def send_order_status_change_email(cls, order, previous_status, new_status, notes=''):
        """Send email notification when order status changes"""
        # Status-specific email subjects and templates
        status_config = {
            'received': {
                'subject': 'Order Received - We Got Your Order!',
                'template': 'order_status_received'
            },
            'pending_payment': {
                'subject': 'Payment Required - Complete Your Order',
                'template': 'order_status_pending_payment'
            },
            'pay_on_delivery': {
                'subject': 'Order Confirmed - Pay on Delivery',
                'template': 'order_status_pay_on_delivery'
            },
            'paid': {
                'subject': 'Payment Confirmed - Thank You!',
                'template': 'order_status_paid'
            },
            'processing': {
                'subject': 'Order Processing - We\'re Preparing Your Items',
                'template': 'order_status_processing'
            },
            'packed_ready': {
                'subject': 'Order Packed - Ready for Dispatch',
                'template': 'order_status_packed_ready'
            },
            'shipped': {
                'subject': 'Order Shipped - On Its Way!',
                'template': 'order_status_shipped'
            },
            'out_for_delivery': {
                'subject': 'Out for Delivery - Almost There!',
                'template': 'order_status_out_for_delivery'
            },
            'delivered': {
                'subject': 'Order Delivered - Enjoy Your Purchase!',
                'template': 'order_status_delivered'
            },
            'completed': {
                'subject': 'Order Completed - Thank You for Your Business!',
                'template': 'order_status_completed'
            },
            'cancelled': {
                'subject': 'Order Cancelled',
                'template': 'order_status_cancelled'
            },
            'returned': {
                'subject': 'Order Return Processed',
                'template': 'order_status_returned'
            }
        }

        config = status_config.get(new_status)
        if not config:
            logger.warning(f"No email configuration for status: {new_status}")
            return False

        # Get estimated delivery date for shipped orders
        estimated_delivery = None
        if new_status == 'shipped' and order.delivery_date:
            estimated_delivery = order.delivery_date
        elif new_status == 'shipped':
            # Estimate 3-5 business days from today
            from datetime import datetime, timedelta
            estimated_delivery = datetime.now().date() + timedelta(days=5)

        # Check if order includes installation services
        installation_required = False
        for item in order.items.all():
            if 'installation' in item.product_name.lower() or 'install' in item.product_name.lower():
                installation_required = True
                break

        # Get order status history for timeline display
        status_history = {}
        for history in order.status_history.order_by('created_at'):
            status_history[history.new_status] = history.created_at

        context = {
            'order': order,
            'customer_name': order.customer.name,
            'order_number': order.order_number,
            'previous_status': previous_status,
            'new_status': new_status,
            'status_display': order.get_status_display(),
            'total_amount': order.total_amount,
            'items': order.items.all(),
            'notes': notes,
            'tracking_number': order.tracking_number,
            'estimated_delivery': estimated_delivery,
            'order_tracking_url': f"https://olivian.co.ke/track/{order.order_number}/",
            'installation_required': installation_required,
            'status_history': status_history,
        }

        subject = f"{config['subject']} - Order #{order.order_number}"

        return cls.send_email_notification(
            config['template'],
            context,
            order.customer.email,
            subject,
            cls.EMAILS['sales']
        )
    
    # Project Notifications
    @classmethod
    def send_project_created_email(cls, project):
        """Notify customer when project is created"""
        context = {
            'project': project,
            'customer_name': project.customer.name,
            'project_number': project.project_number,
        }
        return cls.send_email_notification(
            'project_created',
            context,
            project.customer.email,
            f'New Solar Project #{project.project_number} - Olivian Group',
            cls.EMAILS['admin']
        )
    
    @classmethod
    def send_project_status_update_email(cls, project):
        """Notify customer of project status changes"""
        context = {
            'project': project,
            'customer_name': project.customer.name,
            'project_number': project.project_number,
            'status': project.get_status_display(),
        }
        return cls.send_email_notification(
            'project_status_update',
            context,
            project.customer.email,
            f'Project Update #{project.project_number} - {project.get_status_display()}',
            cls.EMAILS['admin']
        )
    
    # Budget & Payment Notifications
    @classmethod
    def send_payment_reminder_email(cls, payment_schedule):
        """Send payment reminder to customer"""
        context = {
            'payment': payment_schedule,
            'customer_name': payment_schedule.project.customer.name,
            'amount_due': payment_schedule.amount,
            'due_date': payment_schedule.due_date,
        }
        return cls.send_email_notification(
            'payment_reminder',
            context,
            payment_schedule.project.customer.email,
            f'Payment Reminder - {payment_schedule.project.project_number}',
            cls.EMAILS['admin']
        )
    
    # Internal Staff Notifications
    @classmethod
    def send_staff_notification(cls, subject, message, staff_emails=None):
        """Send notification to staff members"""
        if not staff_emails:
            staff_emails = [cls.EMAILS['admin'], cls.EMAILS['info']]
        
        context = {
            'message': message,
            'subject': subject,
        }
        
        for email in staff_emails:
            cls.send_email_notification(
                'staff_notification',
                context,
                email,
                subject,
                cls.EMAILS['admin']
            )
    
    @classmethod
    def send_low_stock_alert(cls, product):
        """Alert staff when product stock is low"""
        context = {
            'product': product,
            'current_stock': product.quantity_available,
            'minimum_stock': product.minimum_stock_level,
        }
        return cls.send_email_notification(
            'low_stock_alert',
            context,
            [cls.EMAILS['admin'], cls.EMAILS['info']],
            f'Low Stock Alert: {product.name}',
            cls.EMAILS['admin']
        )
    
    # Contact Form Email Notifications
    @classmethod
    def send_contact_confirmation(cls, contact_message):
        """Send confirmation email to contact form submitter"""
        context = {
            'contact': contact_message,
            'customer_name': contact_message.full_name,
            'inquiry_type': contact_message.get_inquiry_type_display(),
        }
        context.update(cls.get_company_context())
        
        return cls.send_email_notification(
            'contact_confirmation',
            context,
            contact_message.email,
            f'Thank you for contacting {context["company_name"]}',
            cls.EMAILS['info']
        )
    
    @classmethod
    def send_newsletter_welcome(cls, subscriber):
        """Send welcome email to new newsletter subscriber"""
        context = {
            'subscriber': subscriber,
            'subscriber_name': subscriber.get_full_name(),
            'unsubscribe_url': subscriber.get_unsubscribe_url(),
        }
        context.update(cls.get_company_context())

        return cls.send_email_notification(
            'newsletter_welcome',
            context,
            subscriber.email,
            f'Welcome to {context["company_name"]} Newsletter',
            cls.EMAILS['info']
        )
    
    @classmethod
    def send_contact_notification_to_admin(cls, contact_message):
        """Send new contact message notification to admin"""
        context = {
            'contact': contact_message,
            'customer_name': contact_message.full_name,
            'inquiry_type': contact_message.get_inquiry_type_display(),
            'submission_time': contact_message.submitted_at,
        }
        context.update(cls.get_company_context())
        
        return cls.send_email_notification(
            'contact_admin_notification',
            context,
            [cls.EMAILS['admin'], cls.EMAILS['info']],
            f'New Contact Form Submission - {contact_message.get_inquiry_type_display()}',
            cls.EMAILS['noreply']
        )
    
    @classmethod
    def send_contact_response_email(cls, contact_message, response_message, admin_user):
        """Send response email to contact message author"""
        context = {
            'contact_message': contact_message,
            'response_message': response_message,
            'customer_name': contact_message.full_name,
            'inquiry_type_display': contact_message.get_inquiry_type_display(),
            'admin_name': admin_user.get_full_name() or admin_user.username,
        }
        context.update(cls.get_company_context())
        
        subject = f"Re: Your {contact_message.get_inquiry_type_display()} Inquiry - {context['company_name']}"
        
        success = cls.send_email_notification(
            'contact_response',
            context,
            contact_message.email,
            subject,
            cls.EMAILS['info']
        )
        
        if success:
            # Update the contact message response tracking
            contact_message.is_responded = True
            contact_message.save(update_fields=['is_responded'])
        
        return success
    
    # Notification System Emails
    @classmethod
    def send_notification_email(cls, notification):
        """Send email for a notification object"""
        context = {
            'notification': notification,
            'user_name': notification.user.get_full_name() or notification.user.username,
            'title': notification.title,
            'message': notification.message,
            'link_url': notification.link_url,
            'link_text': notification.link_text,
            'category': notification.get_category_display(),
        }
        context.update(cls.get_company_context())
        
        success = cls.send_email_notification(
            'notification',
            context,
            notification.user.email,
            f'{notification.title} - {context["company_name"]}',
            cls.EMAILS['noreply']
        )
        
        if success:
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
        
        return success
    
    @classmethod
    def send_admin_notification(cls, subject, message, user=None):
        """Send notification email to admin"""
        context = {
            'subject': subject,
            'message': message,
            'user_name': user.get_full_name() or user.username if user else 'System',
            'timestamp': timezone.now(),
        }
        context.update(cls.get_company_context())

        return cls.send_email_notification(
            'admin_notification',
            context,
            cls.EMAILS['admin'],
            f'{subject} - {context["company_name"]}',
            cls.EMAILS['noreply']
        )

    # CRM Email Methods
    @classmethod
    def send_crm_email(cls, subject, content, recipient_email, sender=None,
                      attachments=None, track_opens=False):
        """Send email from CRM with advanced features"""
        try:
            from_email = sender.email if sender else getattr(settings, 'CRM_EMAIL_FROM', cls.EMAILS['sales'])

            # Get signature from settings
            signature = getattr(settings, 'CRM_EMAIL_SIGNATURE', f"""
Best regards,
{sender.get_full_name() if sender else 'CRM Team'}
{sender.role_display() if sender else 'Customer Service'}
{getattr(settings, 'COMPANY_NAME', 'The Olivian Group')}
""").strip()

            context = {
                'content': content,
                'signature': signature,
                'sender': sender,
            }
            context.update(cls.get_company_context())

            email = cls.send_email_notification(
                'crm_email',
                context,
                recipient_email,
                subject,
                from_email
            )

            # Log the email if tracking is enabled
            if email and track_opens:
                cls.log_crm_email(subject, content, recipient_email, sender, 'crm_email')

            return email

        except Exception as e:
            logger.error(f"Failed to send CRM email: {str(e)}")
            return False

    @classmethod
    def log_crm_email(cls, subject, content, recipient, sender, email_type):
        """Log CRM email for tracking purposes"""
        try:
            from apps.crm.models import EmailLog
            EmailLog.objects.create(
                subject=subject,
                content=content,
                recipient=recipient,
                sender=sender,
                email_type=email_type,
                status='sent'
            )
        except Exception as e:
            logger.error(f"Failed to log CRM email: {str(e)}")

    # Lead and Opportunity Email Templates
    @classmethod
    def send_lead_qualification_email(cls, lead):
        """Send lead qualification follow-up email"""
        context = {
            'lead': lead,
            'contact_name': lead.contact.get_full_name(),
            'company_name': lead.company.name if lead.company else 'Your Organization',
            'qualification_url': f"https://olivian.co.ke/crm/leads/{lead.pk}/qualify/",
        }
        context.update(cls.get_company_context())

        subject = f"Next Steps for Your Solar Project - {context['company_name']}"

        return cls.send_email_notification(
            'lead_qualification',
            context,
            lead.contact.email,
            subject,
            cls.EMAILS['sales']
        )

    @classmethod
    def send_opportunity_proposal_email(cls, opportunity, proposal_content):
        """Send detailed proposal to opportunity contact"""
        context = {
            'opportunity': opportunity,
            'proposal_content': proposal_content,
            'contact_name': opportunity.contact.get_full_name(),
            'company_name': opportunity.company.name if opportunity.company else 'Your Organization',
            'proposal_url': f"https://olivian.co.ke/proposals/{opportunity.pk}/",
        }
        context.update(cls.get_company_context())

        subject = f"Detailed Solar Solution Proposal - {opportunity.name}"

        return cls.send_email_notification(
            'opportunity_proposal',
            context,
            opportunity.contact.email,
            subject,
            cls.EMAILS['sales']
        )

    @classmethod
    def send_follow_up_reminder_email(cls, activity):
        """Send follow-up reminder email to assigned user"""
        context = {
            'activity': activity,
            'contact_name': activity.contact.get_full_name(),
            'activity_type': activity.get_activity_type_display(),
            'scheduled_date': activity.scheduled_datetime,
            'activity_url': f"https://olivian.co.ke/crm/activities/{activity.pk}/",
        }
        context.update(cls.get_company_context())

        subject = f"Follow-up Reminder: {activity.subject}"

        return cls.send_email_notification(
            'follow_up_reminder',
            context,
            activity.assigned_to.email,
            subject,
            cls.EMAILS['noreply']
        )

    @classmethod
    def send_campaign_email(cls, campaign, contacts, template_content):
        """Send bulk campaign email to multiple contacts"""
        sent_count = 0
        failed_count = 0

        for contact in contacts:
            context = {
                'campaign': campaign,
                'contact': contact,
                'template_content': template_content,
                'unsubscribe_url': f"https://olivian.co.ke/unsubscribe/{contact.email}/",
            }
            context.update(cls.get_company_context())

            # Personalize the email
            personalized_subject = campaign.subject_template.replace('[NAME]', contact.get_full_name())
            personalized_content = template_content.replace('[NAME]', contact.get_full_name())

            context['personalized_content'] = personalized_content
            context['personalized_subject'] = personalized_subject

            try:
                email = cls.send_email_notification(
                    'campaign_email',
                    context,
                    contact.email,
                    personalized_subject,
                    campaign.from_email or cls.EMAILS['sales']
                )

                if email:
                    sent_count += 1
                    # Log campaign email
                    cls.log_campaign_email(campaign, contact, personalized_subject, personalized_content)
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Failed to send campaign email to {contact.email}: {str(e)}")
                failed_count += 1

        return sent_count, failed_count

    @classmethod
    def log_campaign_email(cls, campaign, contact, subject, content):
        """Log campaign email for analytics"""
        try:
            from apps.crm.models import CampaignEmail
            CampaignEmail.objects.create(
                campaign=campaign,
                contact=contact,
                subject=subject,
                content=content,
                status='sent'
            )
        except Exception as e:
            logger.error(f"Failed to log campaign email: {str(e)}")

    @classmethod
    def send_meeting_reminder_email(cls, activity):
        """Send meeting reminder email 24 hours before scheduled meeting"""
        context = {
            'activity': activity,
            'contact_name': activity.contact.get_full_name(),
            'meeting_time': activity.scheduled_datetime,
            'meeting_location': activity.location or 'To be confirmed',
            'meeting_url': f"https://olivian.co.ke/crm/activities/{activity.pk}/",
        }
        context.update(cls.get_company_context())

        subject = f"Meeting Reminder: {activity.subject}"

        return cls.send_email_notification(
            'meeting_reminder',
            context,
            [activity.contact.email, activity.assigned_to.email],
            subject,
            cls.EMAILS['sales']
        )

    @classmethod
    def send_quote_requested_follow_up(cls, lead):
        """Send follow-up email when quote was requested"""
        context = {
            'lead': lead,
            'contact_name': lead.contact.get_full_name(),
            'request_date': lead.created_at,
            'quote_url': f"https://olivian.co.ke/quotations/{lead.pk}/",
        }
        context.update(cls.get_company_context())

        subject = f"Thank you for your quote request - Next Steps"

        return cls.send_email_notification(
            'quote_requested_follow_up',
            context,
            lead.contact.email,
            subject,
            cls.EMAILS['sales']
        )
