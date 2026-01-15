from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.crm.models import EmailTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default email templates for automated CRM emails'

    def handle(self, *args, **options):
        """Create default email templates for the CRM system"""

        self.stdout.write('Setting up default CRM email templates...')

        # Get the first superuser or create system user for templates
        try:
            system_user = User.objects.filter(is_active=True).first()
        except:
            system_user = None

        # Default email templates with their content
        email_templates = [
            {
                'name': 'Welcome Email',
                'subject': 'Welcome {{contact_first_name}} - Thank you for your interest',
                'body': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to Olivian Solar</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1>Welcome to Olivian Solar</h1>
        <h2>Hello {{contact_first_name}}!</h2>
        <p>Thank you for reaching out to Olivian Group Limited. We're excited to help you discover solar energy solutions.</p>
        <p>Our sales team will review your requirements within 24 hours.</p>
        <div style="background: #f0f0f0; padding: 15px; margin: 20px 0;">
            <p>Contact us:</p>
            <p>Phone: +254 719 728 666</p>
            <p>Email: info@olivian.co.ke</p>
        </div>
    </div>
</body>
</html>
''',
                'template_type': 'welcome',
            },

            {
                'name': 'Lead Nurturing Email',
                'subject': 'Following up on your solar inquiry - {{contact_first_name}}',
                'body': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Following up on your inquiry</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1>Following Up</h1>
        <h2>Hello {{contact_first_name}},</h2>
        <p>I hope this email finds you well. I wanted to follow up on our previous discussion.</p>
        {% if system_type %}
        <p>You were interested in our {{system_type}} solar solution.</p>
        {% endif %}
        <p>Our team has over 8 years of experience in solar design and installation.</p>
        <div style="background: #e8f5e8; padding: 15px; margin: 20px 0;">
            <h3>Why choose Olivian Solar?</h3>
            <ul>
                <li>Experienced professional team</li>
                <li>Premium solar panels and batteries</li>
                <li>Complete installation service</li>
                <li>5-year warranty included</li>
            </ul>
        </div>
        <p>Let's schedule a free consultation call.</p>
        <div style="background: #f0f0f0; padding: 15px; margin: 20px 0;">
            <p>Call us: +254 719 728 666</p>
            <p>Email: info@olivian.co.ke</p>
        </div>
    </div>
</body>
</html>
''',
                'template_type': 'lead_nurture',
            },

            {
                'name': 'Proposal Email',
                'subject': 'Your Solar Solution Proposal - {{contact_first_name}}',
                'body': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Your Solar Proposal</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1>Your Solar Solution Proposal</h1>
        <h2>Hello {{contact_first_name}},</h2>
        <p>Thank you for giving us the opportunity to prepare this detailed solar solution proposal.</p>
        {% if estimated_value %}
        <div style="background: #e8f5e8; padding: 15px; margin: 20px 0;">
            <p><strong>Estimated Value:</strong> {{estimated_value}}</p>
            <p><strong>Expected Payback Period:</strong> 4-6 years</p>
        </div>
        {% endif %}
        <p>This proposal includes:</p>
        <ul>
            <li>Complete system design and specifications</li>
            <li>Detailed cost breakdown</li>
            <li>Professional installation</li>
            <li>5-year warranty</li>
        </ul>
        <p>Please contact us to discuss the next steps.</p>
        <div style="background: #f0f0f0; padding: 15px; margin: 20px 0;">
            <p>Phone: +254 719 728 666</p>
            <p>Email: info@olivian.co.ke</p>
        </div>
    </div>
</body>
</html>
''',
                'template_type': 'proposal',
            },
        ]

        created_count = 0

        for template_data in email_templates:
            # Check if template already exists
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'subject': template_data['subject'],
                    'body': template_data['body'],
                    'template_type': template_data['template_type'],
                    'is_active': True,
                    'created_by': system_user,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f"✓ Created email template: {template.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully created {created_count} CRM email templates"
            )
        )

        if created_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  All email templates already exist. No new templates created."
                )
            )

        # Print summary of templates
        all_templates = EmailTemplate.objects.filter(is_active=True)
        self.stdout.write("\n📧 Available email templates:")
        for template in all_templates.order_by('template_type'):
            self.stdout.write(
                f"  • {template.name} ({template.template_type})"
            )
