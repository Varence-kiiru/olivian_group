from django.core.management.base import BaseCommand
from apps.core.models import CompanySettings
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Populate CompanySettings with optimized sales-driven content'

    def handle(self, *args, **options):
        # Get or create the singleton settings object
        settings, created = CompanySettings.objects.get_or_create(
            pk=1,
            defaults={}
        )

        # Update with optimized sales content
        settings.hero_title = "Save KES 150,000+ on Your First Year - Go Solar Today!"
        settings.hero_subtitle = "Join 500+ Kenyan homeowners who cut electricity bills by 75% with professional solar installations. Complete system design, financing & installation - starts from KES 250,000. Payback in 3-5 years!"
        settings.hero_disclaimer = "Professional site assessment and 10-year warranty included. Government-approved installer with REA certification. Payback period: 3-5 years based on your current KPLC bills."

        # Urgency elements
        settings.urgency_banner_enabled = True
        settings.urgency_banner_text = "🔥 LIMITED TIME: Get FREE installation feasibility assessment this month! Book your consultation before December 31st."
        settings.urgency_banner_end_date = date.today() + timedelta(days=30)

        # Enhanced statistics for credibility
        settings.hero_featured_customers_count = "500+"
        settings.projects_completed = "100+"
        settings.total_capacity = "1.5MW+"
        settings.customer_satisfaction = "98.5%"
        settings.founded_year = 2020

        # Testimonial section
        settings.testimonial_section_title = "What Our Customers Say"
        settings.testimonial_section_subtitle = "Real stories from real Kenyans who chose solar energy with Olivian Solar and never looked back"

        # Social proof messaging
        settings.tagline = "Kenya's Leading Solar Energy Solutions Provider"
        settings.about_description = "Olivian Solar is Kenya's trusted solar energy partner, serving homeowners and businesses across Nairobi, Mombasa, Kisumu, and beyond. With over 100 successful installations and 98.5% customer satisfaction, we deliver rooftop solar systems that save you money while contributing to a sustainable future."

        # Contact and trust elements
        settings.mission_statement = "To accelerate Kenya's transition to clean energy by making solar power affordable, accessible, and profitable for every household and business."

        # Marketing-driven phone and messaging
        settings.sales_phone = "+254-719-728-666"
        settings.whatsapp_number = "+254-719-728-666"

        # Location-specific messaging
        settings.google_maps_url = "https://goo.gl/maps/kahawa-sukari-nairobi"

        # Save the optimized settings
        settings.save()

        self.stdout.write(
            self.style.SUCCESS('Successfully updated CompanySettings with optimized sales content')
        )
