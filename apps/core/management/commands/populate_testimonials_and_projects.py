from django.core.management.base import BaseCommand
from apps.core.models import ContactMessage, ProjectShowcase, TeamMember
from datetime import date

class Command(BaseCommand):
    help = 'Populate testimonials and project showcases with sales-driven content'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample testimonials...')

        # Create sample contact messages (high-converting testimonials)
        testimonials_data = [
            {
                'first_name': 'James',
                'last_name': 'Mwangi',
                'email': 'james.mwangi@gmail.com',
                'phone': '+254712345678',
                'inquiry_type': 'quotation',
                'message': 'I installed a 5kW system last year and my electricity bill went from KES 45,000 to KES 8,000 monthly. The payback was incredible - within 4 years I\'m saving money. Olivian Solar guided me through everything.',
                'location': 'Karen, Nairobi',
                'property_type': 'residential',
                'monthly_bill': 45000,
                'agree_privacy': True,
            },
            {
                'first_name': 'Grace',
                'last_name': 'Wanjiku',
                'email': 'grace.wanjiku@yahoo.com',
                'phone': '+254723456789',
                'inquiry_type': 'general',
                'message': 'After getting solar from Olivian, I never worry about KPLC power cuts anymore. My 3kW system powers everything from lights to water heating. The team was professional and the installation was seamless.',
                'location': 'Runda, Nairobi',
                'property_type': 'residential',
                'monthly_bill': 25000,
                'agree_privacy': True,
            },
            {
                'first_name': 'David',
                'last_name': 'Njoroge',
                'email': 'david.njoroge@outlook.com',
                'phone': '+254734567890',
                'inquiry_type': 'commercial',
                'message': 'As a small business owner, the solar installation has transformed my operations. No more generator fuel costs for my 10kW system. Olivian Solar helped me get financing and the ROI has been outstanding.',
                'location': 'Westlands, Nairobi',
                'property_type': 'commercial',
                'monthly_bill': 65000,
                'agree_privacy': True,
            }
        ]

        for testimonial_data in testimonials_data:
            ContactMessage.objects.get_or_create(
                email=testimonial_data['email'],
                defaults=testimonial_data
            )
            ContactMessage.objects.filter(email=testimonial_data['email']).update(is_read=True)

        self.stdout.write('Creating sample project showcases...')

        # Create project showcases
        projects_data = [
            {
                'title': 'Karen Luxury Home Solar Installation',
                'description': 'Complete 8kW off-grid solar system with battery storage. This family reduced their electricity costs by 85% and gained energy independence during frequent power outages.',
                'location': 'Karen, Nairobi',
                'capacity': '8kW',
                'project_type': 'residential',
                'completion_date': date(2024, 9, 15),
                'is_featured': True,
                'order': 1,
            },
            {
                'title': 'Westlands Restaurant Solar Power',
                'description': '10kW grid-tie solar system helping this busy restaurant cut energy costs by 70%. The system generates surplus power that they sell back to KPLC through net metering.',
                'location': 'Westlands, Nairobi',
                'capacity': '10kW',
                'project_type': 'commercial',
                'completion_date': date(2024, 10, 22),
                'is_featured': True,
                'order': 2,
            },
            {
                'title': 'Nyali Beachfront Villa',
                'description': '5kW solar installation with ocean view optimization. This coastal property now enjoys reliable power 24/7, even during extended power cuts that plague coastal areas.',
                'location': 'Nyali, Mombasa',
                'capacity': '5kW',
                'project_type': 'residential',
                'completion_date': date(2024, 11, 5),
                'is_featured': True,
                'order': 3,
            },
            {
                'title': 'Kilimani Apartment Complex',
                'description': '25kW community solar system serving 50 apartments. Each resident sees reduced electricity costs while the building generates income from excess power production.',
                'location': 'Kilimani, Nairobi',
                'capacity': '25kW',
                'project_type': 'residential',
                'completion_date': date(2024, 8, 30),
                'is_featured': True,
                'order': 4,
            }
        ]

        for project_data in projects_data:
            ProjectShowcase.objects.get_or_create(
                title=project_data['title'],
                location=project_data['location'],
                defaults=project_data
            )

        self.stdout.write('Creating team members...')

        # Create team members for credibility
        team_data = [
            {
                'name': 'Samuel Koinange',
                'position': 'Lead Solar Engineer & CEO',
                'bio': 'Over 8 years in renewable energy with expertise in photovoltaic systems design and installation. Certified by Kenya Renewable Energy Association (REA).',
                'email': 'samuel@olivian.co.ke',
                'order': 1,
                'is_active': True,
            },
            {
                'name': 'Esther Wambui',
                'position': 'Operations Manager',
                'bio': 'Manages project execution and client relationships. Ensures every installation meets the highest standards and exceeds customer expectations.',
                'email': 'esther@olivian.co.ke',
                'order': 2,
                'is_active': True,
            },
            {
                'name': 'Francis Kiprop',
                'position': 'Technical Specialist',
                'bio': 'Electrical engineer specializing in solar system optimization and maintenance. Ensures maximum efficiency and longevity of all installations.',
                'email': 'francis@olivian.co.ke',
                'order': 3,
                'is_active': True,
            }
        ]

        for member_data in team_data:
            TeamMember.objects.get_or_create(
                name=member_data['name'],
                position=member_data['position'],
                defaults=member_data
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated testimonials, project showcases, and team members with sales-optimized content')
        )
