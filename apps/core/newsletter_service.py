"""
Newsletter Campaign Management Service
Handles newsletter creation, sending, and tracking
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from .models import NewsletterCampaign, NewsletterSubscriber, NewsletterSendLog
from .email_utils import EmailService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NewsletterService:
    """Service for managing newsletter campaigns"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    def send_campaign(self, campaign, user=None):
        """Send a newsletter campaign to all target subscribers"""
        try:
            # Validate campaign
            if not campaign.can_send():
                return {
                    'success': False,
                    'error': 'Campaign cannot be sent. Check status and content.'
                }
            
            # Get target subscribers
            subscribers = campaign.get_target_subscribers()
            if not subscribers.exists():
                return {
                    'success': False,
                    'error': 'No active subscribers found for target audience.'
                }
            
            # Update campaign status
            campaign.status = 'sending'
            campaign.save()
            
            # Send to each subscriber
            sent_count = 0
            failed_count = 0
            
            for subscriber in subscribers:
                try:
                    result = self.send_to_subscriber(campaign, subscriber)
                    if result['success']:
                        sent_count += 1
                    else:
                        failed_count += 1
                        logger.error(f"Failed to send to {subscriber.email}: {result['error']}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Exception sending to {subscriber.email}: {str(e)}")
            
            # Update campaign status and stats
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.total_recipients = subscribers.count()  # Total targeted subscribers
            campaign.total_sent = sent_count  # Successfully sent count
            campaign.total_failed = failed_count  # Failed sends
            campaign.save()
            
            return {
                'success': True,
                'recipients': sent_count,
                'failed': failed_count,
                'message': f'Campaign sent to {sent_count} subscribers'
            }
            
        except Exception as e:
            campaign.status = 'draft'  # Reset status on error
            campaign.save()
            logger.error(f"Campaign send failed: {str(e)}")
            return {
                'success': False,
                'error': f'Campaign send failed: {str(e)}'
            }
    
    def send_to_subscriber(self, campaign, subscriber):
        """Send newsletter to individual subscriber"""
        try:
            # Create or get send log
            send_log, created = NewsletterSendLog.objects.get_or_create(
                campaign=campaign,
                subscriber=subscriber,
                defaults={
                    'email_address': subscriber.email,
                    'delivery_status': 'pending'
                }
            )
            
            if not created and send_log.delivery_status == 'sent':
                return {'success': True, 'message': 'Already sent'}
            
            # Generate unsubscribe link
            unsubscribe_url = self.generate_unsubscribe_url(subscriber)
            
            # Prepare context for template
            context = {
                'campaign': campaign,
                'subscriber': subscriber,
                'subscriber_name': subscriber.get_full_name(),
                'unsubscribe_url': unsubscribe_url,
                'tracking_pixel_url': self.generate_tracking_pixel_url(send_log),
                'click_tracking_url': self.generate_click_tracking_url(send_log),
            }
            context.update(self.email_service.get_company_context())

            # Render campaign content as template to enable personalization variables
            try:
                rendered_content = Template(campaign.content).render(Context(context))
                context['rendered_content'] = rendered_content
            except Exception as e:
                logger.warning(f"Failed to render campaign content as template: {str(e)}")
                # Fallback to original content if template rendering fails
                context['rendered_content'] = campaign.content
            
            # Render email content with fallback to default template
            try:
                html_content = render_to_string(f'emails/newsletter_{campaign.template_type}.html', context)
                text_content = render_to_string(f'emails/newsletter_{campaign.template_type}.txt', context)
            except Exception as e:
                # Fallback to default template if specific template doesn't exist
                logger.warning(f"Template newsletter_{campaign.template_type} not found, using default: {str(e)}")
                html_content = render_to_string('emails/newsletter_default.html', context)
                text_content = render_to_string('emails/newsletter_default.txt', context)

            # Create email
            email = EmailMultiAlternatives(
                subject=campaign.subject,
                body=text_content,
                from_email=self.email_service.EMAILS['info'],
                to=[subscriber.email]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email and validate success
            try:
                sent_count = email.send()
                if sent_count > 0:
                    # Update send log
                    send_log.delivery_status = 'sent'
                    send_log.save()
                    return {'success': True, 'message': 'Sent successfully'}
                else:
                    # Email sending failed
                    send_log.delivery_status = 'failed'
                    send_log.error_message = 'Email send returned 0 recipients'
                    send_log.save()
                    return {'success': False, 'error': 'Email send returned 0 recipients'}
            except Exception as send_error:
                # Email sending failed
                send_log.delivery_status = 'failed'
                send_log.error_message = f'Send error: {str(send_error)}'
                send_log.save()
                return {'success': False, 'error': f'Send error: {str(send_error)}'}
            
        except Exception as e:
            # Update send log with error
            if 'send_log' in locals():
                send_log.delivery_status = 'failed'
                send_log.error_message = str(e)
                send_log.save()
            
            return {'success': False, 'error': str(e)}
    
    def generate_unsubscribe_url(self, subscriber):
        """Generate secure unsubscribe URL"""
        token = subscriber.get_unsubscribe_token()
        site_url = getattr(settings, 'SITE_URL', 'https://olivian.co.ke')
        return f"{site_url}{reverse('core:unsubscribe', kwargs={'token': token, 'subscriber_id': subscriber.id})}"
    
    def generate_tracking_pixel_url(self, send_log):
        """Generate tracking pixel URL for open tracking"""
        site_url = getattr(settings, 'SITE_URL', 'https://olivian.co.ke')
        return f"{site_url}{reverse('core:track_open', kwargs={'log_id': send_log.id})}"
    
    def generate_click_tracking_url(self, send_log):
        """Generate click tracking URL"""
        site_url = getattr(settings, 'SITE_URL', 'https://olivian.co.ke')
        return f"{site_url}{reverse('core:track_click', kwargs={'log_id': send_log.id})}"
    
    def track_email_open(self, log_id):
        """Track email open"""
        try:
            send_log = NewsletterSendLog.objects.get(id=log_id)
            if not send_log.opened_at:
                send_log.opened_at = timezone.now()
                send_log.save()
                
                # Update campaign stats
                campaign = send_log.campaign
                campaign.opens_count += 1
                campaign.save()
                
            return True
        except NewsletterSendLog.DoesNotExist:
            return False
    
    def track_email_click(self, log_id, redirect_url=None):
        """Track email click"""
        try:
            send_log = NewsletterSendLog.objects.get(id=log_id)
            if not send_log.clicked_at:
                send_log.clicked_at = timezone.now()
                send_log.save()
                
                # Update campaign stats
                campaign = send_log.campaign
                campaign.clicks_count += 1
                campaign.save()
            
            return redirect_url or campaign.call_to_action_url
        except NewsletterSendLog.DoesNotExist:
            return None
    
    def process_unsubscribe(self, subscriber_id, token):
        """Process newsletter unsubscribe"""
        try:
            subscriber = NewsletterSubscriber.objects.get(id=subscriber_id, is_active=True)
            
            # Verify token
            if subscriber.get_unsubscribe_token() != token:
                return {'success': False, 'error': 'Invalid unsubscribe token'}
            
            # Unsubscribe
            subscriber.is_active = False
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save()
            
            return {
                'success': True,
                'subscriber': subscriber,
                'message': 'Successfully unsubscribed from newsletter'
            }
            
        except NewsletterSubscriber.DoesNotExist:
            return {'success': False, 'error': 'Subscriber not found'}
    
    def subscribe_email(self, email, first_name='', last_name='', source='website_footer'):
        """Add new newsletter subscriber"""
        try:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'source': source,
                    'is_active': True
                }
            )

            message = ''
            was_reactivated = False

            if not created and not subscriber.is_active:
                # Reactivate if previously unsubscribed
                subscriber.is_active = True
                subscriber.unsubscribed_at = None
                subscriber.save()
                created = True  # Treat as new subscription
                was_reactivated = True
                message = 'Welcome back! Your subscription has been reactivated.'
            elif not created and subscriber.is_active:
                # Already active subscriber
                message = 'You are already subscribed to our newsletter.'
            else:
                # New subscriber
                message = 'Thank you for subscribing to our newsletter!'

            if created:
                # Send welcome email for new subscriptions and reactivations
                self.email_service.send_newsletter_welcome(subscriber)

            return {
                'success': True,
                'subscriber': subscriber,
                'is_new': created,
                'was_reactivated': was_reactivated,
                'message': message
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_campaign_analytics(self, campaign):
        """Get detailed analytics for a campaign"""
        send_logs = campaign.send_logs.all()
        
        return {
            'total_sent': send_logs.count(),
            'total_opens': send_logs.filter(opened_at__isnull=False).count(),
            'total_clicks': send_logs.filter(clicked_at__isnull=False).count(),
            'total_unsubscribes': send_logs.filter(unsubscribed_at__isnull=False).count(),
            'open_rate': campaign.open_rate,
            'click_rate': campaign.click_rate,
            'delivery_status': {
                status: send_logs.filter(delivery_status=status).count()
                for status, _ in NewsletterSendLog._meta.get_field('delivery_status').choices
            }
        }
