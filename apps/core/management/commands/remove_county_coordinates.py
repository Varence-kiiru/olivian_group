"""
Management command to remove coordinates from county-type service areas.
Counties should not have point coordinates - only towns should.
"""

from django.core.management.base import BaseCommand
from apps.core.models import ServiceArea


class Command(BaseCommand):
    help = 'Remove coordinates from county-type service areas'

    def handle(self, *args, **options):
        self.stdout.write('Removing coordinates from county service areas...')

        # Get all county-type areas with coordinates
        county_areas = ServiceArea.objects.filter(
            area_type='county',
            latitude__isnull=False
        )

        updated_count = 0
        for area in county_areas:
            self.stdout.write(f'Removing coordinates from: {area.name} ({area.county})')
            area.latitude = None
            area.longitude = None
            area.center_point = None
            area.save(update_fields=['latitude', 'longitude', 'center_point'])
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully removed coordinates from {updated_count} county areas.'
            )
        )

        # Show summary
        total_counties = ServiceArea.objects.filter(area_type='county').count()
        counties_with_coords = ServiceArea.objects.filter(
            area_type='county',
            latitude__isnull=False
        ).count()

        self.stdout.write(f'Total counties: {total_counties}')
        self.stdout.write(f'Counties with coordinates: {counties_with_coords}')
        self.stdout.write(f'Counties without coordinates: {total_counties - counties_with_coords}')
