from django.core.management.base import BaseCommand
from core.models import PolicyPage, FAQItem, Certification
from django.utils.text import slugify
from datetime import date

class Command(BaseCommand):
    help = 'Creates default content for policy pages, FAQs, and certifications if they do not exist'

    def handle(self, *args, **options):
        self.create_default_policies()
        self.create_default_faqs()
        self.create_default_certifications()
        
    def create_default_policies(self):
        policy_defaults = [
            {
                'type': 'privacy',
                'title': 'Privacy Policy',
                'content': '<h2>Privacy Policy</h2><p>This is a default privacy policy. Please update this content in the admin panel.</p>'
            },
            {
                'type': 'terms',
                'title': 'Terms & Conditions',
                'content': '<h2>Terms & Conditions</h2><p>This is a default terms and conditions page. Please update this content in the admin panel.</p>'
            },
            {
                'type': 'refund',
                'title': 'Return & Refund Policy',
                'content': '<h2>Return & Refund Policy</h2><p>This is a default return and refund policy. Please update this content in the admin panel.</p>'
            },
            {
                'type': 'shipping',
                'title': 'Shipping & Delivery',
                'content': '<h2>Shipping & Delivery</h2><p>This is a default shipping and delivery information page. Please update this content in the admin panel.</p>'
            },
            {
                'type': 'faq',
                'title': 'Frequently Asked Questions',
                'content': '<h2>Frequently Asked Questions</h2><p>Below you\'ll find answers to the most common questions about our products and services.</p>'
            },
            {
                'type': 'environment',
                'title': 'Environmental Commitment',
                'content': '<h2>Our Environmental Commitment</h2><p>This is a default environmental commitment page. Please update this content in the admin panel.</p>'
            },
            {
                'type': 'certifications',
                'title': 'Certifications & Standards',
                'content': '<h2>Our Certifications & Standards</h2><p>This is a default certifications page. Please update this content in the admin panel.</p>'
            },
        ]
        
        created_count = 0
        for policy in policy_defaults:
            # Check if a policy of this type exists
            if not PolicyPage.objects.filter(type=policy['type']).exists():
                PolicyPage.objects.create(
                    title=policy['title'],
                    type=policy['type'],
                    content=policy['content'],
                    slug=slugify(policy['title']),
                    is_published=True
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created {policy['title']}"))
        
        if created_count:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} default policy pages"))
        else:
            self.stdout.write(self.style.SUCCESS("All policy pages already exist"))
    
    def create_default_faqs(self):
        # Only create default FAQs if none exist
        if FAQItem.objects.exists():
            self.stdout.write(self.style.SUCCESS("FAQ items already exist - skipping defaults"))
            return
            
        faq_defaults = [
            {
                'question': 'What payment methods do you accept?',
                'answer': '<p>We accept all major credit cards, PayPal, and bank transfers for business customers.</p>',
                'category': 'Payment',
                'order': 1
            },
            {
                'question': 'How long does shipping take?',
                'answer': '<p>Domestic shipping typically takes 3-5 business days. International shipping can take 7-14 business days depending on the destination.</p>',
                'category': 'Shipping',
                'order': 1
            },
            {
                'question': 'What is your return policy?',
                'answer': '<p>We offer a 30-day return policy for most products. Please visit our Return & Refund Policy page for more details.</p>',
                'category': 'Returns',
                'order': 1
            },
            {
                'question': 'Do you ship internationally?',
                'answer': '<p>Yes, we ship to most countries worldwide. Shipping costs and delivery times vary by location.</p>',
                'category': 'Shipping',
                'order': 2
            },
            {
                'question': 'How can I track my order?',
                'answer': '<p>Once your order ships, you will receive a tracking number via email that you can use to monitor your delivery status.</p>',
                'category': 'Orders',
                'order': 1
            },
        ]
        
        created_count = 0
        for faq in faq_defaults:
            FAQItem.objects.create(
                question=faq['question'],
                answer=faq['answer'],
                category=faq['category'],
                order=faq['order']
            )
            created_count += 1
        
        if created_count:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} default FAQ items"))
    
    def create_default_certifications(self):
        # Only create default certifications if none exist
        if Certification.objects.exists():
            self.stdout.write(self.style.SUCCESS("Certifications already exist - skipping defaults"))
            return
            
        certification_defaults = [
            {
                'name': 'ISO 9001',
                'description': '<p>ISO 9001 is the international standard for a quality management system (QMS). We have implemented this standard to demonstrate our ability to consistently provide products that meet customer and regulatory requirements.</p>',
                'issuing_authority': 'International Organization for Standardization',
                'issue_date': date(2022, 1, 15),
                'expiry_date': date(2025, 1, 14),
                'order': 1
            },
            {
                'name': 'Environmental Management System',
                'description': '<p>Our environmental management system is certified to ISO 14001 standards, demonstrating our commitment to minimizing our environmental impact and continuously improving our sustainability practices.</p>',
                'issuing_authority': 'International Organization for Standardization',
                'issue_date': date(2022, 3, 10),
                'expiry_date': date(2025, 3, 9),
                'order': 2
            },
            {
                'name': 'Occupational Health and Safety',
                'description': '<p>We are committed to providing a safe and healthy workplace for all our employees and have been certified for our occupational health and safety management systems.</p>',
                'issuing_authority': 'Occupational Safety and Health Administration',
                'issue_date': date(2022, 5, 20),
                'expiry_date': date(2025, 5, 19),
                'order': 3
            },
        ]
        
        created_count = 0
        for cert in certification_defaults:
            Certification.objects.create(
                name=cert['name'],
                description=cert['description'],
                issuing_authority=cert['issuing_authority'],
                issue_date=cert['issue_date'],
                expiry_date=cert['expiry_date'],
                order=cert['order']
            )
            created_count += 1
        
        if created_count:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} default certifications"))
