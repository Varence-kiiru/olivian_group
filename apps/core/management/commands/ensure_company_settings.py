from django.core.management.base import BaseCommand
from apps.core.models import CompanySettings


class Command(BaseCommand):
    help = 'Ensures company settings exist in the database'

    def handle(self, *args, **options):
        """Create or update company settings"""
        try:
            # Use get_settings to create settings if they don't exist
            settings = CompanySettings.get_settings()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Company settings ensured: {settings.name}'
                )
            )
            
            # Display current settings
            self.stdout.write('\nCurrent Company Settings:')
            self.stdout.write(f'  Name: {settings.name}')
            self.stdout.write(f'  Email: {settings.email}')
            self.stdout.write(f'  Phone: {settings.phone}')
            self.stdout.write(f'  Website: {settings.website}')
            self.stdout.write(f'  Address: {settings.address}')
            self.stdout.write(f'  Primary Color: {settings.primary_color}')
            self.stdout.write(f'  Secondary Color: {settings.secondary_color}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error ensuring company settings: {str(e)}'
                )
            )
            raise e
