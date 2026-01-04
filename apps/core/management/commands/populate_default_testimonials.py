from django.core.management.base import BaseCommand
from apps.core.models import Testimonial

class Command(BaseCommand):
    help = 'Populate default testimonials from static template content'

    def handle(self, *args, **options):
        # Default testimonials based on the static content in home.html
        testimonials_data = [
            {
                'author_name': 'Mohammed K.',
                'author_initials': 'MK',
                'location': 'Westlands, Nairobi',
                'quote': 'The team was professional from start to finish. Our electricity bills dropped by 75% in the first month. Highly recommend!',
                'rating': 5,
                'order': 1,
            },
            {
                'author_name': 'Ann W.',
                'author_initials': 'AW',
                'location': 'Karen, Nairobi',
                'quote': 'Best investment we\'ve made. Professional installation, excellent support, and the savings are incredible. Our family is very happy.',
                'rating': 5,
                'order': 2,
            },
            {
                'author_name': 'David M.',
                'author_initials': 'DM',
                'location': 'Parklands, Nairobi',
                'quote': 'Outstanding service from start to finish. The system works perfectly and has already saved us thousands in electricity costs. Highly recommended!',
                'rating': 5,
                'order': 3,
            },
            {
                'author_name': 'Sarah K.',
                'author_initials': 'SK',
                'location': 'Lang\'ata, Nairobi',
                'quote': 'The installation was smooth and the team was very knowledgeable. We\'re saving about KES 12,000 per month on our electricity bill. Great investment!',
                'rating': 5,
                'order': 4,
            },
            {
                'author_name': 'Peter N.',
                'author_initials': 'PN',
                'location': 'Junction Mall, Nairobi',
                'quote': 'From consultation to installation, everything was handled professionally. The ROI is excellent and the system reliability is outstanding.',
                'rating': 5,
                'order': 5,
            }
        ]

        created_count = 0
        for testimonial_data in testimonials_data:
            testimonial, created = Testimonial.objects.get_or_create(
                author_name=testimonial_data['author_name'],
                location=testimonial_data['location'],
                defaults=testimonial_data
            )
            if created:
                created_count += 1

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} default testimonials')
            )
        else:
            self.stdout.write(
                self.style.WARNING('All default testimonials already exist')
            )
