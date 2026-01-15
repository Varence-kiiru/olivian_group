"""
Management command to populate all Kenyan counties in the ServiceArea table.
"""

from django.core.management.base import BaseCommand
from apps.core.models import ServiceArea


class Command(BaseCommand):
    help = 'Populate all Kenyan counties in the ServiceArea table'

    def handle(self, *args, **options):
        self.stdout.write('Populating Kenyan counties...')

        # List of all 47 Kenyan counties
        kenyan_counties = [
            'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu',
            'Garissa', 'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho',
            'Kiambu', 'Kilifi', 'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui',
            'Kwale', 'Laikipia', 'Lamu', 'Machakos', 'Makueni', 'Mandera',
            'Marsabit', 'Meru', 'Migori', 'Mombasa', 'Murang\'a', 'Nairobi',
            'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua', 'Nyeri',
            'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River', 'Tharaka-Nithi',
            'Trans Nzoia', 'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot'
        ]

        created_count = 0
        existing_count = 0

        for county_name in kenyan_counties:
            area, created = ServiceArea.objects.get_or_create(
                name=county_name,
                area_type='county',
                defaults={
                    'county': county_name,  # Set county field to itself for counties
                    'coverage_type': 'primary',
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created: {county_name}')
                created_count += 1
            else:
                existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Population completed: {created_count} created, {existing_count} already existed'
            )
        )
