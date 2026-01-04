"""
Management command to populate sample contact information for service areas.
"""

from django.core.management.base import BaseCommand
from apps.core.models import ServiceArea


class Command(BaseCommand):
    help = 'Populate sample contact information for service areas'

    def handle(self, *args, **options):
        self.stdout.write('Populating sample contact information for service areas...')

        # Sample contact information by county
        county_contacts = {
            'Nairobi': {
                'Westlands': {'person': 'John Kamau', 'phone': '+254-700-123-456'},
                'Karen': {'person': 'Mary Wanjiku', 'phone': '+254-700-123-457'},
                'Kilimani': {'person': 'David Oduya', 'phone': '+254-700-123-458'},
                'Koinange Street': {'person': 'Grace Achieng', 'phone': '+254-700-123-459'},
                'River Road': {'person': 'Peter Njoroge', 'phone': '+254-700-123-460'},
                'Parklands': {'person': 'Sarah Muthoni', 'phone': '+254-700-123-461'},
                'Lang\'ata': {'person': 'Michael Kiprop', 'phone': '+254-700-123-462'},
            },
            'Mombasa': {
                'Mombasa CBD': {'person': 'Ahmed Hassan', 'phone': '+254-701-234-567'},
                'Likoni': {'person': 'Fatuma Omar', 'phone': '+254-701-234-568'},
                'Changamwe': {'person': 'Juma Mwanga', 'phone': '+254-701-234-569'},
                'Kisauni': {'person': 'Amina Said', 'phone': '+254-701-234-570'},
                'Nyali': {'person': 'Salim Ali', 'phone': '+254-701-234-571'},
            },
            'Kisumu': {
                'Kisumu CBD': {'person': 'Thomas Oduor', 'phone': '+254-702-345-678'},
                'Kondele': {'person': 'Beatrice Atieno', 'phone': '+254-702-345-679'},
                'Nyalenda': {'person': 'George Owino', 'phone': '+254-702-345-680'},
                'Maseno': {'person': 'Ann Nyambura', 'phone': '+254-702-345-681'},
            },
            'Nakuru': {
                'Nakuru CBD': {'person': 'Samuel Chege', 'phone': '+254-703-456-789'},
                'Gilgil': {'person': 'James Kipkoech', 'phone': '+254-703-456-791'},
                'Molo': {'person': 'Caroline Cheruiyot', 'phone': '+254-703-456-792'},
            },
            'Uasin Gishu': {
                'Eldoret': {'person': 'Richard Koech', 'phone': '+254-704-567-890'},
            },
        }

        updated_count = 0
        skipped_count = 0

        # Update towns with specific contact info
        for county_name, town_contacts in county_contacts.items():
            for town_name, contact_info in town_contacts.items():
                try:
                    area = ServiceArea.objects.get(
                        name=town_name,
                        area_type='town',
                        county=county_name,
                        is_active=True
                    )

                    if not area.contact_person or area.contact_person.startswith(town_name):
                        area.contact_person = contact_info['person']
                        area.contact_phone = contact_info['phone']
                        area.save(update_fields=['contact_person', 'contact_phone'])
                        self.stdout.write(f'Updated: {town_name} ({county_name}) - {contact_info["person"]}')
                        updated_count += 1
                    else:
                        skipped_count += 1

                except ServiceArea.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Town not found: {town_name} in {county_name}')
                    )

        # Update remaining towns with generic contact info
        remaining_towns = ServiceArea.objects.filter(
            area_type='town',
            is_active=True,
            contact_person__isnull=True
        ).exclude(
            name__in=['Thika', 'Naivasha']  # Skip existing towns that might have different data
        )

        generic_contacts = [
            {'person': 'Local Service Manager', 'phone': '+254-700-000-000'},
            {'person': 'Area Coordinator', 'phone': '+254-701-000-000'},
            {'person': 'Regional Representative', 'phone': '+254-702-000-000'},
            {'person': 'Field Operations Lead', 'phone': '+254-703-000-000'},
            {'person': 'Service Point Manager', 'phone': '+254-704-000-000'},
        ]

        contact_index = 0
        for town in remaining_towns:
            contact_info = generic_contacts[contact_index % len(generic_contacts)]
            town.contact_person = contact_info['person']
            town.contact_phone = contact_info['phone']
            town.save(update_fields=['contact_person', 'contact_phone'])
            updated_count += 1
            contact_index += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Contact information population completed: {updated_count} updated, {skipped_count} skipped'
            )
        )
