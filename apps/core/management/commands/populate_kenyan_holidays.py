"""
Management command to populate Kenyan holidays for automated offers.
"""
from django.core.management.base import BaseCommand
from apps.core.models import KenyanHoliday, HolidayOffer


class Command(BaseCommand):
    help = 'Populate Kenyan holidays and sample offers for automated banner display'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of holidays (removes existing)')
        parser.add_argument(
            '--with-offers',
            action='store_true',
            help='Also populate sample holiday offers')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing Kenyan holidays...'))

        if options['force']:
            deleted_holidays = KenyanHoliday.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_holidays[0]} existing holidays'))

        # National Holidays (Fixed Dates)
        national_holidays = [
            {
                'name': 'Labour Day',
                'date_type': 'fixed',
                'fixed_month': 5,
                'fixed_day': 1,
                'lead_time_days': 7,
                'duration_days': 1,
                'description': 'International Workers Day',
                'emoji': '🏭'
            },
            {
                'name': 'Madaraka Day',
                'date_type': 'fixed',
                'fixed_month': 6,
                'fixed_day': 1,
                'lead_time_days': 14,
                'duration_days': 1,
                'description': 'Celebration of self-government',
                'emoji': '🇰🇪'
            },
            {
                'name': 'Moi Day',
                'date_type': 'fixed',
                'fixed_month': 10,
                'fixed_day': 10,
                'lead_time_days': 14,
                'duration_days': 1,
                'description': 'Birthday of former President Daniel arap Moi',
                'emoji': '🎂'
            },
            {
                'name': 'Mashujaa Day',
                'date_type': 'fixed',
                'fixed_month': 10,
                'fixed_day': 20,
                'lead_time_days': 14,
                'duration_days': 1,
                'description': 'Heroes Day',
                'emoji': '🌟'
            },
            {
                'name': 'Jamhuri Day',
                'date_type': 'fixed',
                'fixed_month': 12,
                'fixed_day': 12,
                'lead_time_days': 14,
                'duration_days': 1,
                'description': 'Republic Day',
                'emoji': '🏛️'
            }
        ]

        # Religious Holidays (Variable Dates)
        religious_holidays = [
            {
                'name': 'Easter',
                'date_type': 'calculated',
                'lead_time_days': 21,
                'duration_days': 7,
                'description': 'Good Friday through Easter Monday',
                'emoji': '🐣'
            },
            {
                'name': 'Eid al-Fitr',
                'date_type': 'variable',
                'lead_time_days': 7,
                'duration_days': 3,
                'description': 'End of Ramadan (actual dates vary by Islamic calendar)',
                'emoji': '🌙'
            },
            {
                'name': 'Eid al-Adha',
                'date_type': 'variable',
                'lead_time_days': 7,
                'duration_days': 4,
                'description': 'Islamic holy day (actual dates vary by Islamic calendar)',
                'emoji': '🐐'
            },
            {
                'name': 'Christmas/New Year',
                'date_type': 'variable',
                'lead_time_days': 21,
                'duration_days': 28,
                'description': 'December 25 through January 1',
                'emoji': '🎄'
            }
        ]

        created_count = 0
        for holiday_data in national_holidays + religious_holidays:
            holiday, created = KenyanHoliday.objects.get_or_create(
                name=holiday_data['name'],
                defaults=holiday_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'+ Created holiday: {holiday.name}'))
            else:
                self.stdout.write(f'• Holiday already exists: {holiday.name}')

        self.stdout.write(self.style.SUCCESS(f'\nCreated {created_count} new holidays'))

        # Create sample offers if requested
        if options['with_offers']:
            self.create_sample_offers()

        self.stdout.write(self.style.SUCCESS('Kenyan holidays initialization complete!'))

    def create_sample_offers(self):
        """Create sample holiday offers"""
        self.stdout.write(self.style.SUCCESS('\nCreating sample holiday offers...'))

        sample_offers = [
            {
                'holiday_name': 'Christmas/New Year',
                'banner_text': 'Christmas Solar Savings - 25% OFF Complete Systems',
                'discount_percentage': 25.00,
                'discount_description': 'Special holiday discount on all solar installations',
                'special_benefits': 'FREE installation assessment + Extended warranty'
            },
            {
                'holiday_name': 'Easter',
                'banner_text': 'Spring Energy Renewal - 20% OFF Solar Upgrades',
                'discount_percentage': 20.00,
                'discount_description': 'Renew your home with solar power this Easter',
                'special_benefits': 'FREE energy audit + Spring installation discounts'
            },
            {
                'holiday_name': 'Labour Day',
                'banner_text': 'Workplace Solar Solutions - 15% OFF Commercial Systems',
                'discount_percentage': 15.00,
                'discount_description': 'Employee benefits and workplace sustainability',
                'special_benefits': 'FREE workplace energy assessment'
            },
            {
                'holiday_name': 'Madaraka Day',
                'banner_text': 'National Solar Celebration - KES 50,000 OFF',
                'discount_percentage': None,  # Fixed discount
                'discount_description': 'Celebrate Kenya with renewable energy',
                'special_benefits': 'FREE Independence solar consultation'
            },
            {
                'holiday_name': 'Moi Day',
                'banner_text': 'Community Solar Projects - 10% OFF',
                'discount_percentage': 10.00,
                'discount_description': 'Join community solar initiatives',
                'special_benefits': 'Community solar group discounts'
            },
            {
                'holiday_name': 'Mashujaa Day',
                'banner_text': 'Heroes Solar Initiative - 30% OFF',
                'discount_percentage': 30.00,
                'discount_description': 'Renewable energy for Kenya\'s heroes',
                'special_benefits': 'FREE BrandNew Day solar assessment + Military discounts'
            },
            {
                'holiday_name': 'Jamhuri Day',
                'banner_text': 'Republic Solar Savings - 20% OFF All Systems',
                'discount_percentage': 20.00,
                'discount_description': 'Power Kenya\'s future with solar energy',
                'special_benefits': 'FREE Republic Day solar consultation'
            }
        ]

        offers_created = 0
        for offer_data in sample_offers:
            try:
                holiday = KenyanHoliday.objects.get(name=offer_data['holiday_name'])
                offer, created = HolidayOffer.objects.get_or_create(
                    holiday=holiday,
                    banner_text=offer_data['banner_text'],
                    defaults={
                        'discount_percentage': offer_data['discount_percentage'],
                        'discount_description': offer_data['discount_description'],
                        'special_benefits': offer_data['special_benefits'],
                        'priority': 1
                    }
                )
                if created:
                    offers_created += 1
                    self.stdout.write(self.style.SUCCESS(f'+ Created offer: {offer.banner_text[:50]}...'))
                else:
                    self.stdout.write(f'• Offer already exists: {offer.banner_text[:50]}...')

            except KenyanHoliday.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'- Holiday not found: {offer_data["holiday_name"]}')
                )

        self.stdout.write(self.style.SUCCESS(f'\nCreated {offers_created} sample holiday offers'))
        self.stdout.write(
            self.style.SUCCESS('\n>>> Holiday offer automation is now active!')
        )
        self.stdout.write(
            self.style.WARNING('Note: Variable holidays (Eid prayers) use approximate dates.')
        )
        self.stdout.write(
            self.style.WARNING('Update these dates annually based on Islamic calendar.')
        )
