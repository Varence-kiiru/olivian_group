"""
Management command to load default Privacy Policy and Terms of Service content
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import LegalDocument, CookieCategory, CookieDetail


class Command(BaseCommand):
    help = 'Load default Privacy Policy and Terms of Service documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing documents',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']
        
        # Default Privacy Policy content
        privacy_policy_content = """
        <h2>Privacy Policy</h2>
        <p><strong>Last Updated:</strong> {date}</p>
        
        <h3>1. Information We Collect</h3>
        <p>We collect information you provide directly to us, such as when you create an account, make a purchase, or contact us for support.</p>
        
        <h3>2. How We Use Your Information</h3>
        <ul>
            <li>To provide, maintain, and improve our services</li>
            <li>To process transactions and send related information</li>
            <li>To send you technical notices and support messages</li>
            <li>To respond to your comments and questions</li>
        </ul>
        
        <h3>3. Information Sharing</h3>
        <p>We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy.</p>
        
        <h3>4. Data Security</h3>
        <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.</p>
        
        <h3>5. Your Rights</h3>
        <p>You have the right to access, update, or delete your personal information. You may also opt out of certain communications from us.</p>
        
        <h3>6. Contact Us</h3>
        <p>If you have any questions about this Privacy Policy, please contact us at info@olivian.co.ke</p>
        """.format(date=timezone.now().strftime('%B %d, %Y'))
        
        # Default Terms of Service content
        terms_content = """
        <h2>Terms of Service</h2>
        <p><strong>Last Updated:</strong> {date}</p>
        
        <h3>1. Acceptance of Terms</h3>
        <p>By accessing and using this website, you accept and agree to be bound by the terms and provision of this agreement.</p>
        
        <h3>2. Services</h3>
        <p>The Olivian Group Limited provides professional solar solutions including consultation, installation, and maintenance services.</p>
        
        <h3>3. User Accounts</h3>
        <p>When you create an account with us, you must provide information that is accurate, complete, and current at all times.</p>
        
        <h3>4. Products and Services</h3>
        <ul>
            <li>All product descriptions and pricing are subject to change without notice</li>
            <li>We reserve the right to refuse service to anyone for any reason</li>
            <li>Installation services are subject to site assessment and local regulations</li>
        </ul>
        
        <h3>5. Payment Terms</h3>
        <p>Payment is due according to the terms specified in your quotation or agreement. We accept various payment methods including M-Pesa.</p>
        
        <h3>6. Warranty and Liability</h3>
        <p>Our solar products and installations come with manufacturer and workmanship warranties as specified in your agreement.</p>
        
        <h3>7. Governing Law</h3>
        <p>These terms shall be governed by and construed in accordance with the laws of Kenya.</p>
        
        <h3>8. Contact Information</h3>
        <p>For questions about these Terms of Service, contact us at info@olivian.co.ke or +254-719-728-666</p>
        """.format(date=timezone.now().strftime('%B %d, %Y'))
        
        # Cookie Policy content
        cookie_policy_content = """
        <h2>Cookie Policy</h2>
        <p><strong>Last Updated:</strong> {date}</p>
        
        <h3>What are cookies?</h3>
        <p>Cookies are small text files that are placed on your computer or mobile device when you visit our website.</p>
        
        <h3>How we use cookies</h3>
        <ul>
            <li><strong>Essential cookies:</strong> Required for the website to function properly</li>
            <li><strong>Analytics cookies:</strong> Help us understand how visitors use our website</li>
            <li><strong>Functionality cookies:</strong> Remember your preferences and settings</li>
        </ul>
        
        <h3>Managing cookies</h3>
        <p>You can control and/or delete cookies as you wish through your browser settings.</p>
        
        <h3>Contact us</h3>
        <p>If you have questions about our use of cookies, contact us at info@olivian.co.ke</p>
        """.format(date=timezone.now().strftime('%B %d, %Y'))
        
        # Create or update documents
        documents = [
            {
                'document_type': 'privacy_policy',
                'title': 'Privacy Policy',
                'content': privacy_policy_content,
                'short_description': 'Learn how we collect, use, and protect your personal information.',
            },
            {
                'document_type': 'terms_of_service', 
                'title': 'Terms of Service',
                'content': terms_content,
                'short_description': 'Terms and conditions for using our website and services.',
            },
            {
                'document_type': 'cookie_policy',
                'title': 'Cookie Policy', 
                'content': cookie_policy_content,
                'short_description': 'Information about how we use cookies on our website.',
            }
        ]
        
        for doc_data in documents:
            document, created = LegalDocument.objects.get_or_create(
                document_type=doc_data['document_type'],
                defaults={
                    'title': doc_data['title'],
                    'content': doc_data['content'],
                    'short_description': doc_data['short_description'],
                    'effective_date': timezone.now().date(),
                    'version': '1.0',
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created {doc_data["title"]}')
                )
            elif overwrite:
                document.title = doc_data['title']
                document.content = doc_data['content']
                document.short_description = doc_data['short_description']
                document.version = '1.1'
                document.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {doc_data["title"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{doc_data["title"]} already exists (use --overwrite to update)')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Legal documents setup completed!')
        )
        
        # Load default cookie categories and details
        self.load_cookie_categories()

    def load_cookie_categories(self):
        """Load default cookie categories and sample cookie details"""
        categories_data = [
            {
                'name': 'essential',
                'display_name': 'Essential Cookies',
                'description': 'These cookies are necessary for the website to function and cannot be disabled.',
                'is_essential': True,
                'order': 1,
                'cookies': [
                    {
                        'name': 'sessionid',
                        'purpose': 'Maintains your session while browsing the website',
                        'duration': 'Session (deleted when browser closes)',
                        'provider': 'First Party',
                        'third_party': False
                    },
                    {
                        'name': 'csrftoken',
                        'purpose': 'Prevents cross-site request forgery attacks',
                        'duration': '1 year',
                        'provider': 'First Party',
                        'third_party': False
                    }
                ]
            },
            {
                'name': 'analytics',
                'display_name': 'Analytics Cookies',
                'description': 'Help us understand how visitors interact with our website by collecting anonymous information.',
                'is_essential': False,
                'order': 2,
                'cookies': [
                    {
                        'name': '_ga',
                        'purpose': 'Distinguishes unique users for Google Analytics',
                        'duration': '2 years',
                        'provider': 'Google',
                        'third_party': True
                    },
                    {
                        'name': '_ga_*',
                        'purpose': 'Used by Google Analytics 4 to persist session state',
                        'duration': '2 years',
                        'provider': 'Google',
                        'third_party': True
                    }
                ]
            },
            {
                'name': 'marketing',
                'display_name': 'Marketing Cookies',
                'description': 'Used to track visitors across websites to display relevant advertisements.',
                'is_essential': False,
                'order': 3,
                'cookies': [
                    {
                        'name': '_fbp',
                        'purpose': 'Facebook Pixel tracking for advertising',
                        'duration': '3 months',
                        'provider': 'Facebook',
                        'third_party': True
                    }
                ]
            },
            {
                'name': 'preferences',
                'display_name': 'Preference Cookies',
                'description': 'Remember your preferences and settings to enhance your experience.',
                'is_essential': False,
                'order': 4,
                'cookies': [
                    {
                        'name': 'user_preferences',
                        'purpose': 'Stores your website preferences like theme and language',
                        'duration': '1 year',
                        'provider': 'First Party',
                        'third_party': False
                    }
                ]
            },
            {
                'name': 'social',
                'display_name': 'Social Media Cookies',
                'description': 'Allow you to share content on social media platforms.',
                'is_essential': False,
                'order': 5,
                'cookies': []
            }
        ]
        
        for cat_data in categories_data:
            category, created = CookieCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'display_name': cat_data['display_name'],
                    'description': cat_data['description'],
                    'is_essential': cat_data['is_essential'],
                    'order': cat_data['order'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created cookie category: {cat_data["display_name"]}')
                )
                
                # Create cookie details
                for cookie_data in cat_data['cookies']:
                    CookieDetail.objects.create(
                        name=cookie_data['name'],
                        category=category,
                        purpose=cookie_data['purpose'],
                        duration=cookie_data['duration'],
                        provider=cookie_data['provider'],
                        third_party=cookie_data['third_party'],
                        is_active=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  - Added cookie: {cookie_data["name"]}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Cookie category already exists: {cat_data["display_name"]}')
                )
