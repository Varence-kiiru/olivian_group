from django.core.management.base import BaseCommand
from apps.core.models import CompanySettings

class Command(BaseCommand):
    help = 'Initialize company settings if they do not exist'

    def handle(self, *args, **options):
        if not CompanySettings.objects.exists():
            CompanySettings.objects.create(
                name='The Olivian Group Limited',
                email='info@olivian.co.ke',
                phone='+254-719-728-666',
                website='https://olivian.co.ke',
                address='Nairobi, Kenya',
                primary_color='#38b6ff',
                secondary_color='#ffffff',
                tagline='Professional Solar Solutions',
                about_description='Professional solar solutions for homes and businesses in Kenya.'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created company settings'))
        else:
            self.stdout.write(self.style.SUCCESS('Company settings already exist'))