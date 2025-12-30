"""
Management command to populate major towns/cities for each Kenyan county as service points.
"""

from django.core.management.base import BaseCommand
from apps.core.models import ServiceArea


class Command(BaseCommand):
    help = 'Populate major towns/cities for each Kenyan county as service points'

    def handle(self, *args, **options):
        self.stdout.write('Populating major towns/cities for Kenyan counties...')

        # Major towns/cities for each county (based on population and economic importance)
        county_towns = {
            'Bomet': ['Bomet Town', 'Longisa', 'Sotik'],
            'Bungoma': ['Bungoma Town', 'Webuye', 'Malakisi', 'Kimilili'],
            'Busia': ['Busia Town', 'Malaba', 'Nambale', 'Port Victoria'],
            'Elgeyo-Marakwet': ['Iten', 'Tambach', 'Kapsowar'],
            'Embu': ['Embu Town', 'Runyenjes', 'Kiritiri'],
            'Garissa': ['Garissa Town', 'Ijara', 'Dadaab'],
            'Homa Bay': ['Homa Bay Town', 'Mbita', 'Ndhiwa'],
            'Isiolo': ['Isiolo Town', 'Merti', 'Garbatulla'],
            'Kakamega': ['Kakamega Town', 'Mumias', 'Lugari', 'Butere'],
            'Kajiado': ['Kajiado Town', 'Ongata Rongai', 'Kitengela', 'Kiserian'],
            'Kericho': ['Kericho Town', 'Litein', 'Londiani'],
            'Kiambu': ['Kiambu Town', 'Thika', 'Limuru', 'Ruiru', 'Karuri'],
            'Kilifi': ['Kilifi Town', 'Malindi', 'Watamu', 'Mombasa Road'],
            'Kirinyaga': ['Kerugoya', 'Kutus', 'Sagana'],
            'Kisii': ['Kisii Town', 'Ogembo', 'Suneka'],
            'Kisumu': ['Kisumu CBD', 'Kondele', 'Nyalenda', 'Maseno'],
            'Kitui': ['Kitui Town', 'Mwingi', 'Mukuyuni'],
            'Kwale': ['Kwale Town', 'Ukunda', 'Kinango'],
            'Laikipia': ['Nanyuki', 'Rumuruti', 'Dol Dol'],
            'Machakos': ['Machakos Town', 'Athi River', 'Kangundo'],
            'Makueni': ['Wote', 'Mbitini', 'Emali'],
            'Migori': ['Migori Town', 'Awendo', 'Rongo'],
            'Mombasa': ['Mombasa CBD', 'Likoni', 'Changamwe', 'Kisauni', 'Nyali'],
            'Murang\'a': ['Murang\'a Town', 'Kenol', 'Kahuro'],
            'Nairobi': ['Westlands', 'Karen', 'Kilimani', 'Koinange Street', 'River Road', 'Parklands', 'Lang\'ata'],
            'Nakuru': ['Nakuru CBD', 'Naivasha', 'Gilgil', 'Molo'],
            'Nandi': ['Kapsabet', 'Nandi Hills', 'Mosoriot'],
            'Narok': ['Narok Town', 'Kilgoris', 'Ololulunga'],
            'Nyamira': ['Nyamira Town', 'Keroka', 'Nkubu'],
            'Nyandarua': ['Ol Kalou', 'Ndaragwa', 'Engineer'],
            'Nyeri': ['Nyeri Town', 'Othaya', 'Karatina', 'Nanyuki Road'],
            'Siaya': ['Siaya Town', 'Bondo', 'Usenge'],
            'Taita-Taveta': ['Voi', 'Taveta', 'Wundanyi'],
            'Tharaka-Nithi': ['Chuka', 'Marimanti', 'Mukothima'],
            'Trans Nzoia': ['Kitale', 'Kwanza', 'Endebess'],
            'Uasin Gishu': ['Eldoret', 'Burnt Forest', 'Turbo', 'Moiben'],
            'Vihiga': ['Vihiga Town', 'Chavakali', 'Luanda'],
        }

        # Get excluded counties (same as geocoding command)
        excluded_counties = ['Wajir', 'Mandera', 'Marsabit', 'Samburu', 'Turkana', 'West Pokot', 'Baringo', 'Tana River', 'Lamu']

        created_count = 0
        existing_count = 0

        for county_name, towns in county_towns.items():
            # Skip excluded counties
            if county_name in excluded_counties:
                continue

            # Get the county ServiceArea object
            try:
                county_area = ServiceArea.objects.get(
                    name=county_name,
                    area_type='county',
                    is_active=True
                )
            except ServiceArea.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'County {county_name} not found, skipping towns')
                )
                continue

            for town_name in towns:
                area, created = ServiceArea.objects.get_or_create(
                    name=town_name,
                    area_type='town',
                    defaults={
                        'county': county_name,  # Store county name as string
                        'coverage_type': 'primary',
                        'is_active': True,
                        'description': f'Service point in {town_name}, {county_name} County',
                        'estimated_response_time': '1-2 business days',
                        'contact_person': f'{town_name} Service Manager',
                        'contact_phone': '+254-700-000-000',  # Placeholder phone
                    }
                )
                if created:
                    self.stdout.write(f'Created: {town_name} ({county_name})')
                    created_count += 1
                else:
                    existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Town population completed: {created_count} created, {existing_count} already existed'
            )
        )
