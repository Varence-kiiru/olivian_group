from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.email_utils import EmailService
from django.template.loader import render_to_string

User = get_user_model()

class Command(BaseCommand):
    help = 'Test email verification system'

    def handle(self, *args, **options):
        self.stdout.write("Testing Email Verification System...")
        
        # Test company context
        self.stdout.write("\n1. Testing company context...")
        context = EmailService.get_company_context()
        self.stdout.write(f"Company context: {context}")
        
        # Create a test user (don't save to database)
        self.stdout.write("\n2. Creating test user...")
        test_user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        
        # Test email template rendering
        self.stdout.write("\n3. Testing email template rendering...")
        verification_url = "https://olivian.co.ke/accounts/verify-email/12345/"
        
        email_context = {
            'user_name': test_user.first_name or test_user.username,
            'user_email': test_user.email,
            'verification_url': verification_url,
        }
        email_context.update(EmailService.get_company_context())
        
        try:
            html_content = render_to_string('emails/email_verification.html', email_context)
            self.stdout.write(self.style.SUCCESS("✅ Email template rendered successfully!"))
            self.stdout.write(f"Email preview (first 500 chars):\n{html_content[:500]}...")
            
            # Test sending email (should print to console in DEBUG mode)
            self.stdout.write("\n4. Testing email sending...")
            result = EmailService.send_email_verification(test_user, verification_url)
            self.stdout.write(f"Email send result: {result}")
            
            if result:
                self.stdout.write(self.style.SUCCESS("✅ Email verification system is working!"))
            else:
                self.stdout.write(self.style.ERROR("❌ Email sending failed!"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error rendering template: {e}"))
            import traceback
            traceback.print_exc()
