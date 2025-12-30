from django.core.management.base import BaseCommand
from apps.core.models import CompanySettings

class Command(BaseCommand):
    help = 'Setup initial company settings with proper contact information'

    def handle(self, *args, **options):
        # Get or create company settings with proper defaults
        settings = CompanySettings.get_settings()
        
        self.stdout.write(f"Company settings configured: {settings.name}")
        self.stdout.write(f"Main Phone: {settings.phone}")
        self.stdout.write(f"Email: {settings.email}")
        self.stdout.write(f"Address: {settings.address}")
        
        if settings.sales_phone:
            self.stdout.write(f"Sales Phone: {settings.sales_phone}")
        if settings.support_phone:
            self.stdout.write(f"Support Phone: {settings.support_phone}")
        if settings.whatsapp_number:
            self.stdout.write(f"WhatsApp: {settings.get_whatsapp_url()}")
        
        # Check if social media is configured
        if settings.has_social_media():
            self.stdout.write("Social media links configured:")
            social_links = settings.get_social_media_links()
            for platform, url in social_links.items():
                if url:
                    self.stdout.write(f"  {platform.title()}: {url}")
        else:
            self.stdout.write(self.style.WARNING(
                "No social media links configured. "
                "Add them in Django Admin under Core > Company Settings"
            ))
        
        self.stdout.write(
            self.style.SUCCESS(
                "\nCompany settings are ready! "
                "You can update them in Django Admin under Core > Company Settings"
            )
        )
