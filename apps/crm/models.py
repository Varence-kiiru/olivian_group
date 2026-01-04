from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import logging
import re

# Initialize logger for email functionality
logger = logging.getLogger(__name__)

User = get_user_model()


def sanitize_text_for_database(text):
    """
    Sanitize text to prevent database encoding issues.
    Removes or replaces characters that can't be stored in the current charset.
    """
    if not text:
        return text

    try:
        # Try to encode as UTF-8 to check for problematic characters
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        # Remove characters that can't be encoded
        return re.sub(r'[^\x00-\x7F\u0080-\uFFFF]', '', text)
    except Exception:
        # Fallback: remove non-ASCII characters
        return re.sub(r'[^\x00-\x7F]', '', text)


class LeadSource(models.Model):
    """Source of leads (Website, Referral, Social Media, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Lead Source'
        verbose_name_plural = 'Lead Sources'

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Individual contacts within companies"""
    TITLE_CHOICES = [
        ('mr', 'Mr.'),
        ('mrs', 'Mrs.'),
        ('ms', 'Ms.'),
        ('dr', 'Dr.'),
        ('eng', 'Eng.'),
        ('prof', 'Prof.'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('prospect', 'Prospect'),
        ('customer', 'Customer')
    ]

    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Job title/position")

    # Address information
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Professional details
    linkedin_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contacts_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # New fields
    department = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    country = models.CharField(
        max_length=100,
        default='Kenya',
        blank=True
    )

    # Relationship
    source = models.ForeignKey(
        LeadSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts'
    )
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return full name with title"""
        name_parts = []
        if self.title:
            name_parts.append(self.get_title_display())
        name_parts.extend([self.first_name, self.last_name])
        return ' '.join(name_parts)

    def get_absolute_url(self):
        return reverse('crm:contact_detail', kwargs={'pk': self.pk})


class Company(models.Model):
    """Companies/Organizations"""
    COMPANY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('government', 'Government'),
        ('ngo', 'NGO'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, default='commercial')
    registration_number = models.CharField(max_length=50, blank=True, help_text="Business registration number")
    tax_number = models.CharField(max_length=50, blank=True, help_text="KRA PIN")

    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Address
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Business details
    industry = models.CharField(max_length=100, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)

    # Relationship
    primary_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_company')
    contacts = models.ManyToManyField(Contact, blank=True, related_name='companies')
    
    # Metadata
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='companies_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    country = models.CharField(
        max_length=100,
        default='Kenya',
        blank=True
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('crm:company_detail', kwargs={'pk': self.pk})


class Lead(models.Model):
    """Sales leads"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal Sent'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('unqualified', 'Unqualified'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    SYSTEM_TYPE_CHOICES = [
        ('grid_tied', 'Grid-Tied'),
        ('off_grid', 'Off-Grid'),
        ('hybrid', 'Hybrid'),
        ('backup', 'Backup Power'),
        ('water_heating', 'Solar Water Heating'),
        ('street_lighting', 'Street Lighting'),
    ]
    
    # Basic information
    title = models.CharField(max_length=200, help_text="Lead title/description")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='leads')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='leads')
    
    # Lead details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    source = models.ForeignKey(
        LeadSource, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='leads'  # Add this line
    )
    
    # Solar project details
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPE_CHOICES, blank=True)
    estimated_capacity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Estimated system size in kW")
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Estimated project value in KES")
    monthly_electricity_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Customer's current monthly bill")
    
    # Timeline
    expected_close_date = models.DateField(null=True, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    next_follow_up = models.DateField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    
    # Additional information
    description = models.TextField(blank=True, help_text="Lead description and requirements")
    notes = models.TextField(blank=True, help_text="Internal notes")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='leads_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
    
    def __str__(self):
        return f"{self.title} - {self.contact.get_full_name()}"
    
    def get_absolute_url(self):
        return reverse('crm:lead_detail', kwargs={'pk': self.pk})
    
    @property
    def is_overdue(self):
        """Check if follow-up is overdue"""
        if self.next_follow_up:
            return self.next_follow_up < timezone.now().date()
        return False
    
    @property
    def days_since_created(self):
        """Days since lead was created"""
        return (timezone.now().date() - self.created_at.date()).days

    def save(self, *args, **kwargs):
        # Track status changes for automated emails
        old_status = None
        if self.pk:
            try:
                old_instance = Lead.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Lead.DoesNotExist:
                pass

        # Ensure created_at is timezone-aware if it's being set
        if self.created_at and timezone.is_naive(self.created_at):
            self.created_at = timezone.make_aware(self.created_at)

        # Ensure converted_at is timezone-aware
        if self.status == 'won' and not self.converted_at:
            self.converted_at = timezone.now()

        # Save the instance first
        super().save(*args, **kwargs)

        # Send automated emails based on status changes
        if old_status != self.status and old_status is not None:
            self.send_status_change_email(old_status, self.status)

    def send_status_change_email(self, old_status, new_status):
        """Send automated email based on lead status change"""
        try:
            # Get appropriate template for the new status
            template = self.get_email_template_for_status(new_status)
            if not template:
                logger.warning(f"No email template found for lead status: {new_status}")
                return

            # Prepare template variables
            template_vars = self.get_email_template_variables()

            # Render subject and body
            subject = self.render_template(template.subject, template_vars)
            body = self.render_template(template.body, template_vars)

            # Send email
            from django.core.mail import send_mail
            result = send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@olivian.co.ke'),
                recipient_list=[self.contact.email],
                html_message=body if '<' in body else None,
                fail_silently=True
            )

            if result:
                # Log the email
                EmailLog.objects.create(
                    recipient=self.contact.email,
                    recipient_name=self.contact.get_full_name(),
                    subject=subject,
                    template=template,
                    status='sent',
                    sent_at=timezone.now(),
                    contact=self.contact,
                    lead=self,
                    body=body,
                    sent_by=self.assigned_to
                )
                logger.info(f"Automated email sent to {self.contact.email} for lead status change: {old_status} -> {new_status}")
            else:
                logger.warning(f"Failed to send automated email to {self.contact.email}")

        except Exception as e:
            logger.error(f"Error sending automated email: {str(e)}", exc_info=True)

    def get_email_template_for_status(self, status):
        """Get appropriate email template for lead status"""
        template_mappings = {
            'new': 'welcome',
            'contacted': 'lead_nurture',
            'qualified': 'follow_up',
            'proposal': 'proposal',
            'negotiation': 'follow_up',
            'won': 'thank_you',
            'lost': 'rejection',
            'unqualified': 'rejection'
        }

        template_type = template_mappings.get(status, 'custom')
        try:
            return EmailTemplate.objects.filter(
                template_type=template_type,
                is_active=True
            ).first()
        except Exception:
            return None

    def get_email_template_variables(self):
        """Prepare template variables for email rendering"""
        # Handle assigned_to with default values
        if self.assigned_to:
            # Get proper full name - fallback to username if first/last names not set
            full_name = self.assigned_to.get_full_name()
            if not full_name or full_name.strip() == '':
                # Use username if get_full_name() returns empty
                full_name = self.assigned_to.username
                # Try to make it more presentable
                if full_name and not full_name[0].isupper():
                    full_name = full_name.capitalize()

            assigned_name = full_name
            assigned_phone = self.assigned_to.phone or '+254 719 728 666'  # Company default if no personal phone
            assigned_email = self.assigned_to.email or 'info@olivian.co.ke'  # Company default if no personal email
            # Handle department/bio if available
            assigned_department = self.assigned_to.department or 'Sales Team'
        else:
            assigned_name = 'Your Sales Representative'
            assigned_phone = '+254 719 728 666'  # Company main line
            assigned_email = 'info@olivian.co.ke'  # Company main email
            assigned_department = 'Sales Team'

        return {
            'lead_title': self.title,
            'lead_url': f"https://olivian.co.ke/crm/leads/{self.pk}/" if hasattr(self, 'pk') else '',
            'contact_name': self.contact.get_full_name(),
            'contact_first_name': self.contact.first_name,
            'company_name': self.company.name if self.company else '',
            'estimated_value': f"KES {self.estimated_value:,.0f}" if self.estimated_value else '',
            # Enhanced assigned representative variables
            'assigned_to': assigned_name,
            'assigned_to_phone': assigned_phone,
            'assigned_to_email': assigned_email,
            'assigned_to_department': assigned_department,
            'assigned_to_full_info': f"{assigned_name} ({assigned_department})",
            'assigned_to_contact': f"{assigned_phone} | {assigned_email}",
            # Handle |default filter manually for backward compatibility
            'assigned_to|default:"Your Sales Representative"': assigned_name,
            'expected_close_date': self.expected_close_date.strftime('%B %d, %Y') if self.expected_close_date else '',
            'days_since_created': self.days_since_created,
            'system_type': self.get_system_type_display(),
            'estimated_capacity': f"{self.estimated_capacity} kW" if self.estimated_capacity else '',
            'monthly_electricity_bill': f"KES {self.monthly_electricity_bill:,.0f}" if self.monthly_electricity_bill else '',
            'source': self.source.name if self.source else '',
            'priority': self.get_priority_display(),
            'status': self.get_status_display(),
            'description': self.description or '',
            'company_website': self.company.website if self.company else '',
            'company_phone': self.company.phone if self.company else '',
        }

    def render_template(self, template_text, variables):
        """Render template with variable substitution"""
        try:
            import re
            # Convert Django template syntax {{variable}} to Python template $variable
            # But avoid matching {{if}}, {{endif}}, etc. Django template tags
            def convert_django_to_python(match):
                var_name = match.group(1)
                # Skip if it's a Django template tag (contains if, for, endif, etc.)
                if re.search(r'\b(if|for|endif|endfor|block|extends|include)\b', var_name):
                    return match.group(0)  # Return unchanged
                return f"${var_name}"

            # Convert {{variable_name}} to $variable_name
            converted_text = re.sub(r'\{\{([^}]+)\}\}', convert_django_to_python, template_text)

            # Now use Python's string.Template
            from string import Template
            template = Template(converted_text)
            return template.safe_substitute(**variables)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template_text

    def send_welcome_email(self):
        """Send welcome email to new lead"""
        return self.send_status_change_email(None, 'new')

    def send_follow_up_reminder(self):
        """Send follow-up reminder email"""
        try:
            template = EmailTemplate.objects.filter(
                template_type='follow_up',
                is_active=True
            ).first()

            if not template:
                logger.warning("No follow-up email template found")
                return False

            template_vars = self.get_email_template_variables()
            template_vars['days_inactive'] = self.days_since_created

            subject = self.render_template(template.subject, template_vars)
            body = self.render_template(template.body, template_vars)

            from django.core.mail import send_mail
            result = send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@olivian.co.ke'),
                recipient_list=[self.contact.email],
                html_message=body if '<' in body else None,
                fail_silently=True
            )

            if result:
                EmailLog.objects.create(
                    recipient=self.contact.email,
                    recipient_name=self.contact.get_full_name(),
                    subject=subject,
                    template=template,
                    status='sent',
                    sent_at=timezone.now(),
                    contact=self.contact,
                    lead=self,
                    body=body,
                    sent_by=self.assigned_to
                )
                self.last_contact_date = timezone.now().date()
                self.save(update_fields=['last_contact_date'])
                return True

            return False

        except Exception as e:
            logger.error(f"Error sending follow-up email: {str(e)}", exc_info=True)
            return False


class Opportunity(models.Model):
    """Sales opportunities (qualified leads)"""
    STAGE_CHOICES = [
        ('qualification', 'Qualification'),
        ('needs_analysis', 'Needs Analysis'),
        ('proposal', 'Proposal/Quote'),
        ('negotiation', 'Negotiation'),
        ('decision', 'Decision'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name='opportunity')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunities'  # Add this line
    )
    
    # Sales details
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='qualification')
    probability = models.PositiveIntegerField(default=25, help_text="Probability of closing (0-100%)")
    value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Opportunity value in KES")
    
    # Timeline
    expected_close_date = models.DateField()
    actual_close_date = models.DateField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    
    # Additional details
    description = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)
    competition = models.TextField(blank=True, help_text="Competing companies/solutions")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='opportunities_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-value', 'expected_close_date']
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'
    
    def __str__(self):
        return f"{self.name} - {self.value:,.0f} KES"
    
    def get_absolute_url(self):
        return reverse('crm:opportunity_detail', kwargs={'pk': self.pk})
    
    @property
    def weighted_value(self):
        """Value weighted by probability"""
        from decimal import Decimal
        probability_decimal = Decimal(str(self.probability)) / Decimal('100')
        return self.value * probability_decimal
    
    @property
    def is_overdue(self):
        """Check if opportunity is past expected close date"""
        if self.stage not in ['closed_won', 'closed_lost']:
            return self.expected_close_date < timezone.now().date()
        return False

    # Define consistent stage weights/probabilities as class variables
    STAGE_WEIGHTS = {
        'qualification': {'progress': 20, 'probability': 10},
        'needs_analysis': {'progress': 40, 'probability': 30},
        'proposal': {'progress': 60, 'probability': 50},
        'negotiation': {'progress': 80, 'probability': 70},
        'closed_won': {'progress': 100, 'probability': 100},
        'closed_lost': {'progress': 100, 'probability': 0}
    }

    def change_stage(self, new_stage, user):
        """Change opportunity stage and update probability"""
        old_stage = self.stage
        if new_stage in self.STAGE_WEIGHTS:
            self.stage = new_stage
            self.probability = self.STAGE_WEIGHTS[new_stage]['probability']

            if new_stage in ['closed_won', 'closed_lost']:
                self.actual_close_date = timezone.now().date()

            self.save()

            # Send automated email for stage change
            if old_stage != new_stage:
                self.send_stage_change_email(old_stage, new_stage)

            # Create activity record for stage change
            Activity.objects.create(
                subject=f"Stage changed to {self.get_stage_display()}",
                activity_type='other',
                status='completed',
                opportunity=self,
                contact=self.contact,
                scheduled_datetime=timezone.now(),
                completed_datetime=timezone.now(),
                description=f"Opportunity stage changed to {self.get_stage_display()}",
                assigned_to=self.assigned_to or user,
                created_by=user
            )

    def send_stage_change_email(self, old_stage, new_stage):
        """Send automated email based on opportunity stage change"""
        try:
            # Get appropriate template for the new stage
            template = self.get_email_template_for_stage(new_stage)
            if not template:
                logger.warning(f"No email template found for opportunity stage: {new_stage}")
                return

            # Prepare template variables
            template_vars = self.get_email_template_variables()

            # Render subject and body
            subject = self.render_template(template.subject, template_vars)
            body = self.render_template(template.body, template_vars)

            # Send email
            from django.core.mail import send_mail
            result = send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@olivian.co.ke'),
                recipient_list=[self.contact.email],
                html_message=body if '<' in body else None,
                fail_silently=True
            )

            if result:
                # Log the email
                EmailLog.objects.create(
                    recipient=self.contact.email,
                    recipient_name=self.contact.get_full_name(),
                    subject=subject,
                    template=template,
                    status='sent',
                    sent_at=timezone.now(),
                    contact=self.contact,
                    opportunity=self,
                    body=body,
                    sent_by=self.assigned_to
                )
                logger.info(f"Automated email sent to {self.contact.email} for opportunity stage change: {old_stage} -> {new_stage}")
            else:
                logger.warning(f"Failed to send automated email to {self.contact.email}")

        except Exception as e:
            logger.error(f"Error sending automated email for opportunity stage change: {str(e)}", exc_info=True)

    def get_email_template_for_stage(self, stage):
        """Get appropriate email template for opportunity stage"""
        template_mappings = {
            'qualification': 'lead_nurture',  # Nurturing during qualification
            'needs_analysis': 'follow_up',    # Follow-up on needs analysis
            'proposal': 'proposal',           # Send proposal
            'negotiation': 'follow_up',       # Follow-up during negotiation
            'decision': 'follow_up',          # Check decision status
            'closed_won': 'thank_you',        # Success email
            'closed_lost': 'rejection'        # Closure email
        }

        template_type = template_mappings.get(stage, 'custom')
        try:
            return EmailTemplate.objects.filter(
                template_type=template_type,
                is_active=True
            ).first()
        except Exception:
            return None

    def get_email_template_variables(self):
        """Prepare template variables for opportunity email rendering"""
        # Handle assigned_to with default values
        if self.assigned_to:
            # Get proper full name - fallback to username if first/last names not set
            full_name = self.assigned_to.get_full_name()
            if not full_name or full_name.strip() == '':
                # Use username if get_full_name() returns empty
                full_name = self.assigned_to.username
                # Try to make it more presentable
                if full_name and not full_name[0].isupper():
                    full_name = full_name.capitalize()

            assigned_name = full_name
            assigned_phone = self.assigned_to.phone or '+254 719 728 666'  # Company default if no personal phone
            assigned_email = self.assigned_to.email or 'info@olivian.co.ke'  # Company default if no personal email
        else:
            assigned_name = 'Your Sales Representative'
            assigned_phone = '+254 719 728 666'  # Company main line
            assigned_email = 'info@olivian.co.ke'  # Company main email

        # Get lead information (since opportunity is linked to lead)
        lead_title = ""
        if self.lead:
            lead_title = self.lead.title
            system_type = self.lead.get_system_type_display() if self.lead.system_type else ''
            estimated_capacity = f"{self.lead.estimated_capacity} kW" if self.lead.estimated_capacity else ''
            source = self.lead.source.name if self.lead.source else ''
        else:
            system_type = ''
            estimated_capacity = ''
            source = ''

        return {
            'opportunity_name': self.name,
            'lead_title': lead_title,
            'contact_name': self.contact.get_full_name(),
            'contact_first_name': self.contact.first_name,
            'company_name': self.company.name if self.company else '',
            'opportunity_value': f"KES {self.value:,.0f}" if self.value else '',
            'weighted_value': f"KES {self.weighted_value:,.0f}" if self.weighted_value else '',
            'probability': f"{self.probability}%" if self.probability else '',
            'stage': self.get_stage_display(),
            # Enhanced assigned representative variables
            'assigned_to': assigned_name,
            'assigned_to_phone': assigned_phone,
            'assigned_to_email': assigned_email,
            'expected_close_date': self.expected_close_date.strftime('%B %d, %Y') if self.expected_close_date else '',
            'days_since_created': (timezone.now().date() - self.created_at.date()).days,
            'system_type': system_type,
            'estimated_capacity': estimated_capacity,
            'source': source,
            'description': self.description or '',
            'next_steps': self.next_steps or '',
            'company_website': self.company.website if self.company else '',
            'company_phone': self.company.phone if self.company else '',
        }

    def render_template(self, template_text, variables):
        """Render template with variable substitution"""
        try:
            import re
            # Convert Django template syntax {{variable}} to Python template $variable
            # But avoid matching {{if}}, {{endif}}, etc. Django template tags
            def convert_django_to_python(match):
                var_name = match.group(1)
                # Skip if it's a Django template tag (contains if, for, endif, etc.)
                if re.search(r'\b(if|for|endif|endfor|block|extends|include)\b', var_name):
                    return match.group(0)  # Return unchanged
                return f"${var_name}"

            # Convert {{variable_name}} to $variable_name
            converted_text = re.sub(r'\{\{([^}]+)\}\}', convert_django_to_python, template_text)

            # Now use Python's string.Template
            from string import Template
            template = Template(converted_text)
            return template.safe_substitute(**variables)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template_text


class Activity(models.Model):
    """CRM activities (calls, meetings, emails, etc.)"""
    TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('demo', 'Product Demo'),
        ('site_visit', 'Site Visit'),
        ('proposal', 'Proposal Sent'),
        ('follow_up', 'Follow Up'),
        ('presentation', 'Presentation'),
        ('training', 'Training'),
        ('negotiation', 'Negotiation'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
        ('postponed', 'Postponed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Basic information
    subject = models.CharField(max_length=200, help_text="Brief activity summary")
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', help_text="Activity priority level")

    # Relationships
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='activities')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')

    # Timing
    scheduled_datetime = models.DateTimeField(help_text="When the activity is scheduled")
    end_datetime = models.DateTimeField(null=True, blank=True, help_text="When the activity ends")
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Activity duration in minutes")
    completed_datetime = models.DateTimeField(null=True, blank=True, help_text="When the activity was actually completed")

    # Location & Logistics
    location = models.CharField(max_length=255, blank=True, help_text="Meeting location or venue")
    address = models.TextField(blank=True, help_text="Complete address for the activity")
    meeting_room = models.CharField(max_length=100, blank=True, help_text="Conference room or virtual meeting room")

    # Virtual Meeting Details
    virtual_meeting_link = models.URLField(blank=True, help_text="Video conference link")
    meeting_id = models.CharField(max_length=100, blank=True, help_text="Virtual meeting ID")
    access_code = models.CharField(max_length=50, blank=True, help_text="Access code for virtual meeting")

    # Preparation & Materials
    preparation_notes = models.TextField(blank=True, help_text="What needs to be prepared before this activity")
    materials_needed = models.TextField(blank=True, help_text="Any materials or documents needed")

    # Activity Details
    description = models.TextField(blank=True, help_text="Detailed activity description")
    agenda = models.TextField(blank=True, help_text="Activity agenda or topics to be discussed")
    objectives = models.TextField(blank=True, help_text="Activity goals and objectives")

    # Outcome & Follow-up
    outcome = models.TextField(blank=True, help_text="Activity outcome and results")
    action_items = models.TextField(blank=True, help_text="Specific action items from this activity")
    next_steps = models.TextField(blank=True, help_text="Follow-up actions required")
    follow_up_date = models.DateField(null=True, blank=True, help_text="Next follow-up date")

    # Communication & Notes
    notes = models.TextField(blank=True, help_text="Internal notes about this activity")
    key_discussion_points = models.TextField(blank=True, help_text="Important points discussed")
    decisions_made = models.TextField(blank=True, help_text="Decisions made during this activity")

    # Cost & Resources
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Estimated cost for this activity")
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Actual cost incurred")
    required_resources = models.TextField(blank=True, help_text="Resources required for this activity")

    # Assignment & Participation
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='participated_activities',
        help_text="Users who participated in this activity"
    )

    # Notifications & Reminders
    email_reminder_sent = models.BooleanField(default=False, help_text="Whether email reminder was sent")
    sms_reminder_sent = models.BooleanField(default=False, help_text="Whether SMS reminder was sent")
    last_reminder_sent = models.DateTimeField(null=True, blank=True, help_text="When the last reminder was sent")

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activities_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Categorization & Organization
    category = models.CharField(max_length=100, blank=True, help_text="Activity category for organization")
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")

    # Integration fields
    external_id = models.CharField(max_length=100, blank=True, help_text="ID from external calendar system")
    calendar_synced = models.BooleanField(default=False, help_text="Whether synced with external calendar")

    def save(self, *args, **kwargs):
        # Sanitize text fields to prevent encoding issues
        text_fields = [
            'description', 'notes', 'location', 'address', 'meeting_room',
            'preparation_notes', 'materials_needed', 'agenda', 'objectives',
            'outcome', 'action_items', 'next_steps', 'key_discussion_points',
            'decisions_made', 'required_resources', 'category', 'tags'
        ]

        for field_name in text_fields:
            field_value = getattr(self, field_name, '')
            if field_value:
                setattr(self, field_name, sanitize_text_for_database(str(field_value)))

        # Auto-calculate end time if duration is provided
        if self.scheduled_datetime and self.duration_minutes and not self.end_datetime:
            from datetime import timedelta
            self.end_datetime = self.scheduled_datetime + timedelta(minutes=self.duration_minutes)

        # Auto-update opportunity expected close date if this is a planning activity
        if self.opportunity and self.activity_type in ['proposal', 'negotiation', 'demo']:
            if not self.opportunity.expected_close_date and self.scheduled_datetime:
                self.opportunity.expected_close_date = self.scheduled_datetime.date()
                self.opportunity.save(update_fields=['expected_close_date'])

        super().save(*args, **kwargs)

    def get_video_conference_url(self):
        """Return formatted video conference URL"""
        if self.virtual_meeting_link:
            return self.virtual_meeting_link
        elif self.meeting_id and self.access_code:
            return f"zoom.meeting.com/j/{self.meeting_id}#pwd={self.access_code}"
        return None

    def get_total_cost(self):
        """Return actual cost if available, otherwise estimated"""
        return self.actual_cost or self.estimated_cost or 0

    def get_participant_list(self):
        """Return formatted list of participants"""
        participants = list(self.participants.values_list('get_full_name', flat=True))
        if participants:
            return ', '.join(participants)
        return "None"

    def is_team_meeting(self):
        """Check if this is a team meeting"""
        return self.participants.count() > 1

    def get_reminder_status(self):
        """Get status of reminders"""
        status = []
        if self.email_reminder_sent:
            status.append("Email sent")
        if self.sms_reminder_sent:
            status.append("SMS sent")
        if not status:
            return "No reminders sent"
        return ", ".join(status)

    class Meta:
        ordering = ['-scheduled_datetime']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        indexes = [
            models.Index(fields=['activity_type', 'status']),
            models.Index(fields=['scheduled_datetime', 'assigned_to']),
            models.Index(fields=['contact', 'lead', 'opportunity']),
        ]
    
    class Meta:
        ordering = ['scheduled_datetime']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.subject} - {self.scheduled_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def get_absolute_url(self):
        return reverse('crm:activity_detail', kwargs={'pk': self.pk})


class Campaign(models.Model):
    """Marketing campaigns"""
    TYPE_CHOICES = [
        ('email', 'Email Marketing'),
        ('social', 'Social Media'),
        ('ppc', 'Pay-Per-Click'),
        ('content', 'Content Marketing'),
        ('event', 'Event/Trade Show'),
        ('referral', 'Referral Program'),
        ('print', 'Print Advertising'),
        ('radio', 'Radio'),
        ('tv', 'Television'),
        ('outdoor', 'Outdoor/Billboard'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Budget and targets
    budget = models.DecimalField(max_digits=10, decimal_places=2, help_text="Campaign budget in KES")
    target_leads = models.PositiveIntegerField(help_text="Target number of leads")
    target_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Target revenue in KES")
    
    # Content
    description = models.TextField(blank=True)
    message = models.TextField(blank=True, help_text="Campaign message/content")
    landing_page_url = models.URLField(blank=True)
    
    # Assignment
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='campaigns')
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='campaigns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('crm:campaign_detail', kwargs={'pk': self.pk})
    
    @property
    def actual_leads(self):
        """Count of leads generated by this campaign"""
        # This would be calculated based on lead source tracking
        return self.leads.count() if hasattr(self, 'leads') else 0
    
    @property
    def lead_conversion_rate(self):
        """Lead to opportunity conversion rate"""
        leads_count = self.actual_leads
        if leads_count > 0:
            opportunities_count = sum(1 for lead in self.leads.all() if hasattr(lead, 'opportunity'))
            return (opportunities_count / leads_count) * 100
        return 0


class Pipeline(models.Model):
    """Sales pipeline configuration"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Sales Pipeline'
        verbose_name_plural = 'Sales Pipelines'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default pipeline
            Pipeline.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class PipelineStage(models.Model):
    """Stages within a sales pipeline"""
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    probability = models.PositiveIntegerField(help_text="Default probability for this stage (0-100%)")
    is_closed = models.BooleanField(default=False, help_text="Is this a closed stage (won/lost)")
    is_won = models.BooleanField(default=False, help_text="Is this a won stage")

    class Meta:
        ordering = ['pipeline', 'order']
        unique_together = ['pipeline', 'name']
        verbose_name = 'Pipeline Stage'
        verbose_name_plural = 'Pipeline Stages'

    def __str__(self):
        return f"{self.pipeline.name} - {self.name}"


# New Models for Email Integration and Enhanced Functionality
class EmailTemplate(models.Model):
    """Email templates for different communication scenarios"""
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('lead_nurture', 'Lead Nurturing'),
        ('follow_up', 'Follow-up'),
        ('proposal', 'Proposal'),
        ('thank_you', 'Thank You'),
        ('rejection', 'Rejection'),
        ('meeting_request', 'Meeting Request'),
        # Opportunity-specific templates
        ('opportunity_qualification', 'Opportunity Qualification'),
        ('opportunity_proposal', 'Opportunity Proposal'),
        ('opportunity_negotiation', 'Opportunity Negotiation'),
        ('opportunity_closure', 'Opportunity Closure'),
        ('opportunity_follow_up', 'Opportunity Follow-up'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField(help_text="Email body with {{variable}} placeholders")
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES, default='custom')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='email_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['template_type', 'name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class EmailLog(models.Model):
    """Log of sent emails for tracking and analytics"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('complained', 'Spam Complaint'),
        ('failed', 'Failed'),
    ]

    recipient = models.EmailField()
    recipient_name = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=200)
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    message_id = models.CharField(max_length=255, blank=True)  # For tracking

    # Related objects
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True)

    # Email content
    body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    # Metadata
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_emails')

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        return f"Email to {self.recipient} - {self.subject}"


class Document(models.Model):
    """File attachments and documents for leads and opportunities"""
    DOCUMENT_TYPES = [
        ('proposal', 'Proposal'),
        ('contract', 'Contract'),
        ('invoice', 'Invoice'),
        ('quote', 'Quotation'),
        ('presentation', 'Presentation'),
        ('photo', 'Photo'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='crm_documents/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    description = models.TextField(blank=True)

    # Related objects
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')

    # Version control
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)

    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        # Mark previous versions as not latest
        if self.is_latest and self.pk:
            Document.objects.filter(
                models.Q(contact=self.contact) | models.Q(lead=self.lead) | models.Q(opportunity=self.opportunity) | models.Q(company=self.company)
            ).exclude(pk=self.pk).update(is_latest=False)

        super().save(*args, **kwargs)


class LeadScore(models.Model):
    """Dynamic lead scoring system"""
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name='score')
    total_score = models.PositiveIntegerField(default=0)
    score_breakdown = models.JSONField(default=dict, help_text="Detailed breakdown of scoring factors")
    grade = models.CharField(max_length=1, choices=[
        ('A', 'A - Hot Lead'),
        ('B', 'B - Warm Lead'),
        ('C', 'C - Cold Lead'),
        ('D', 'D - Dead Lead'),
    ], blank=True)
    last_calculated = models.DateTimeField(auto_now=True)
    calculated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Lead Score'
        verbose_name_plural = 'Lead Scores'

    def __str__(self):
        return f"{self.lead.title} - Score: {self.total_score} ({self.grade})"

    def calculate_score(self):
        """Calculate lead score based on various factors"""
        score = 0
        breakdown = {}

        # Company factors
        if self.lead.company:
            company_score = 0
            if self.lead.company.employee_count:
                if self.lead.company.employee_count > 100:
                    company_score += 25  # Large company
                elif self.lead.company.employee_count > 50:
                    company_score += 15  # Medium company
                elif self.lead.company.employee_count > 10:
                    company_score += 10  # Small company
            breakdown['company_size'] = company_score
            score += company_score

        # Budget/estimated value
        if self.lead.estimated_value:
            budget_score = 0
            if self.lead.estimated_value > 500000:  # >500K KES
                budget_score = 30
            elif self.lead.estimated_value > 100000:  # >100K KES
                budget_score = 20
            elif self.lead.estimated_value > 50000:  # >50K KES
                budget_score = 15
            elif self.lead.estimated_value > 10000:  # >10K KES
                budget_score = 10
            breakdown['budget'] = budget_score
            score += budget_score

        # System size/capacity
        if self.lead.estimated_capacity:
            capacity_score = 0
            if self.lead.estimated_capacity >= 50:  # Large system
                capacity_score = 20
            elif self.lead.estimated_capacity >= 20:
                capacity_score = 15
            elif self.lead.estimated_capacity >= 10:
                capacity_score = 10
            elif self.lead.estimated_capacity >= 5:
                capacity_score = 5
            breakdown['capacity'] = capacity_score
            score += capacity_score

        # Activity engagement
        activity_count = self.lead.activities.count()
        activity_score = min(activity_count * 5, 25)  # Max 25 points for activities
        breakdown['activities'] = activity_score
        score += activity_score

        # Source quality scoring
        source_scores = {
            'website': 15,
            'referral': 20,
            'social_media': 10,
            'trade_show': 15,
            'cold_call': 5,
            'advertisement': 8,
        }
        source_score = source_scores.get(getattr(self.lead.source, 'name', '').lower().replace(' ', '_'), 0)
        breakdown['source'] = source_score
        score += source_score

        # Priority bonus
        priority_scores = {
            'urgent': 15,
            'high': 10,
            'medium': 5,
            'low': 0,
        }
        priority_score = priority_scores.get(self.lead.priority, 0)
        breakdown['priority'] = priority_score
        score += priority_score

        # Lead age penalty (older leads get lower scores)
        age_days = (timezone.now().date() - self.lead.created_at.date()).days
        age_penalty = max(0, (age_days // 30) * 5)  # 5 points per month
        age_penalty = min(age_penalty, 25)  # Max 25 points penalty
        breakdown['age_penalty'] = -age_penalty
        score -= age_penalty

        # Cap score between 0 and 100
        score = max(0, min(score, 100))

        # Assign grade based on score
        if score >= 80:
            grade = 'A'
        elif score >= 60:
            grade = 'B'
        elif score >= 30:
            grade = 'C'
        else:
            grade = 'D'

        self.total_score = score
        self.score_breakdown = breakdown
        self.grade = grade
        self.save()

        return score


class Workflow(models.Model):
    """Automated workflows for lead nurturing and task management"""
    WORKFLOW_TYPES = [
        ('lead_nurture', 'Lead Nurturing'),
        ('follow_up', 'Follow-up Sequence'),
        ('birthday', 'Birthday Campaign'),
        ('anniversary', 'Anniversary Campaign'),
        ('reactivation', 'Customer Reactivation'),
        ('custom', 'Custom Workflow'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES, default='custom')
    is_active = models.BooleanField(default=True)

    # Triggers
    trigger_event = models.CharField(max_length=50, choices=[
        ('lead_created', 'Lead Created'),
        ('lead_status_change', 'Lead Status Change'),
        ('opportunity_created', 'Opportunity Created'),
        ('activity_completed', 'Activity Completed'),
        ('date_trigger', 'Date-based Trigger'),
        ('manual', 'Manual Trigger'),
    ], default='manual')

    trigger_conditions = models.JSONField(default=dict, help_text="Conditions for triggering workflow")

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workflow_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"


class WorkflowStep(models.Model):
    """Individual steps within a workflow"""
    ACTION_TYPES = [
        ('send_email', 'Send Email'),
        ('create_task', 'Create Task'),
        ('update_lead', 'Update Lead Status'),
        ('schedule_activity', 'Schedule Activity'),
        ('send_sms', 'Send SMS'),
        ('webhook', 'Webhook Call'),
        ('wait', 'Wait/Delay'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)

    # Action configuration
    action_config = models.JSONField(default=dict, help_text="Configuration for the action")

    # Timing
    delay_days = models.PositiveIntegerField(default=0, help_text="Days to wait before executing")
    delay_hours = models.PositiveIntegerField(default=0, help_text="Hours to wait before executing")

    # Conditions
    conditions = models.JSONField(default=dict, help_text="Conditions for executing this step")

    class Meta:
        ordering = ['workflow', 'order']
        unique_together = ['workflow', 'order']

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.name}"
