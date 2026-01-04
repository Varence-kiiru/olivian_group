"""
Management command to geocode service areas and populate coordinates.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.core.models import ServiceArea
from apps.core.geographic_utils import get_geographic_service
import time


class Command(BaseCommand):
    help = 'Geocode service areas and populate coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-geocoding of areas that already have coordinates',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between geocoding requests (seconds)',
        )
        parser.add_argument(
            '--exclude-counties',
            nargs='*',
            default=['Wajir', 'Mandera', 'Marsabit', 'Samburu', 'Turkana', 'West Pokot', 'Baringo', 'Tana River', 'Lamu'],
            help='Counties to exclude from geocoding',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting service area geocoding...')

        # Get areas to geocode
        if options['force']:
            areas = ServiceArea.objects.filter(is_active=True)
            self.stdout.write(f'Force re-geocoding all {areas.count()} active areas')
        else:
            areas = ServiceArea.objects.filter(
                is_active=True,
                latitude__isnull=True,
                longitude__isnull=True
            )
            self.stdout.write(f'Geocoding {areas.count()} areas without coordinates')

        # Filter out excluded counties
        excluded_counties = [county.lower() for county in options['exclude_counties']]
        areas = areas.exclude(name__iregex=r'^(' + '|'.join(excluded_counties) + ')$')
        self.stdout.write(f'Excluding counties: {", ".join(options["exclude_counties"])}')
        self.stdout.write(f'Final areas to geocode: {areas.count()}')

        geo_service = get_geographic_service()
        delay = options['delay']

        success_count = 0
        error_count = 0

        for area in areas:
            self.stdout.write(f'Geocoding: {area.name} ({area.area_type})')

            # Create location string
            location_string = f"{area.name}, Kenya"

            # Geocode
            geo_result = geo_service.geocode_location(location_string)

            if geo_result:
                area.latitude = geo_result['latitude']
                area.longitude = geo_result['longitude']
                area.save(update_fields=['latitude', 'longitude'])

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {area.name}: {area.latitude}, {area.longitude}'
                    )
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to geocode: {area.name}')
                )
                error_count += 1

            # Add delay to avoid rate limiting
            if delay > 0:
                time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(
                f'Geocoding completed: {success_count} successful, {error_count} failed'
            )
        )
