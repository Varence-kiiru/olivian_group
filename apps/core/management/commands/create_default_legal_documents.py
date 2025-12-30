from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import LegalDocument, CompanySettings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create default legal documents (Data Deletion, Disclaimer, Refund Policy)'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Creating default legal documents...')
        )

        self.create_data_deletion_document()
        self.create_disclaimer_document()
        self.create_refund_policy_document()

        self.stdout.write(
            self.style.SUCCESS('All legal documents created successfully!')
        )

    def get_company_info(self):
        """Get company information for document content"""
        try:
            company = CompanySettings.get_settings()
            return {
                'name': company.name or 'Olivian Group',
                'email': company.email or 'privacy@olivian.co.ke',
                'phone': company.phone or '+254-719-728-666',
                'address': company.address or 'Kahawa Sukari Road, Nairobi, Kenya',
            }
        except Exception as e:
            logger.warning(f'Error getting company info: {e}')
            return {
                'name': 'Olivian Group',
                'email': 'privacy@olivian.co.ke',
                'phone': '+254-719-728-666',
                'address': 'Kahawa Sukari Road, Nairobi, Kenya',
            }

    def create_data_deletion_document(self):
        """Create the Data Deletion document"""
        company = self.get_company_info()

        content = f"""
        <h2>Your Right to Data Deletion</h2>

        <p>At {company['name']}, we respect your privacy and your right to control your personal data. Under applicable data protection laws (including GDPR and similar regulations), you have the right to request the deletion of your personal data that we have collected about you.</p>

        <h3>What is Data Deletion?</h3>

        <p>Data deletion, also known as the "right to erasure," allows you to request that we delete your personal data when:</p>

        <ul>
            <li>The data is no longer necessary for the purposes for which it was collected</li>
            <li>You withdraw your consent (where applicable)</li>
            <li>You object to processing and there are no overriding legitimate grounds</li>
            <li>The data has been unlawfully processed</li>
            <li>Erasure is required to comply with legal obligations</li>
        </ul>

        <h3>How to Request Data Deletion</h3>

        <p>To request deletion of your personal data, please contact us using one of the following methods:</p>

        <h4>Option 1: Email Request</h4>
        <p>Send an email to our Data Protection Officer at:</p>
        <p><strong>Email:</strong> <a href="mailto:{company['email']}">{company['email']}</a></p>
        <p>Please include "Data Deletion Request" in the subject line and provide:</p>
        <ul>
            <li>Your full name</li>
            <li>Your account email address (if applicable)</li>
            <li>Any other identifying information</li>
            <li>A brief description of what data you want deleted</li>
        </ul>

        <h4>Option 2: Phone Request</h4>
        <p>Call our customer service team at:</p>
        <p><strong>Phone:</strong> <a href="tel:{company['phone']}">{company['phone']}</a></p>
        <p>Our team will guide you through the verification process and confirm your request.</p>

        <h4>Option 3: Written Request</h4>
        <p>You can also send a written request to our registered office address. Please mark your envelope "Confidential - Data Deletion Request".</p>

        <h3>Verification Process</h3>

        <p>To protect your privacy and security, we will:</p>
        <ul>
            <li>Verify your identity through appropriate means</li>
            <li>Confirm the scope of data you wish to delete</li>
            <li>Process your request within 30 days (or as required by law)</li>
            <li>Notify you of the outcome of your request</li>
        </ul>

        <h3>What Data Can Be Deleted?</h3>

        <p>We may delete the following types of personal data upon request:</p>
        <ul>
            <li>Account information and profile data</li>
            <li>Contact information and communication history</li>
            <li>Browsing and usage data (where applicable)</li>
            <li>Newsletter subscription data</li>
            <li>Any other personal data we have collected about you</li>
        </ul>

        <h3>Limitations and Exceptions</h3>

        <p>Please note that we may not be able to delete all your data in certain situations, including:</p>
        <ul>
            <li>Legal obligations requiring data retention</li>
            <li>Ongoing contracts or legal proceedings</li>
            <li>Legitimate business needs (e.g., fraud prevention)</li>
            <li>Data that has been anonymized</li>
        </ul>

        <h3>Data Retention After Deletion</h3>

        <p>In some cases, we may retain limited information for legal compliance, including:</p>
        <ul>
            <li>Basic account information for legal compliance</li>
            <li>Anonymized data for statistical purposes</li>
            <li>Records of your deletion request</li>
        </ul>

        <h3>Account Deactivation vs. Data Deletion</h3>

        <p>Please note the difference between:</p>

        <p><strong>Account Deactivation:</strong> Temporarily disables your account. You can reactivate it at any time.</p>

        <p><strong>Data Deletion:</strong> Permanently removes your personal data from our systems. This action cannot be undone.</p>

        <h3>Processing Time</h3>

        <p>We aim to process data deletion requests within 30 days of verification. You will receive confirmation once the process is complete.</p>

        <h3>Contact Information</h3>

        <p>For any questions about this process or your data rights:</p>

        <p><strong>Data Protection Officer</strong><br>
        {company['name']}<br>
        Email: <a href="mailto:{company['email']}">{company['email']}</a><br>
        Phone: <a href="tel:{company['phone']}">{company['phone']}</a></p>

        <p><em>This page was last updated on {timezone.now().date()}</em></p>
        """

        doc, created = LegalDocument.objects.get_or_create(
            document_type='data_deletion',
            defaults={
                'title': 'How to Delete Your Data',
                'content': content,
                'short_description': 'Learn how to request deletion of your personal data from our systems.',
                'version': '1.0',
                'is_active': True,
                'effective_date': timezone.now().date(),
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Created Data Deletion document')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Data Deletion document already exists')
            )

    def create_disclaimer_document(self):
        """Create the Disclaimer document"""
        company = self.get_company_info()

        content = f"""
        <h2>Website Disclaimer</h2>

        <p>The information contained on this website is for general information purposes only. The information is provided by {company['name']} and while we endeavour to keep the information up to date and correct, we make no representations or warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability or availability with respect to the website or the information, products, services, or related graphics contained on the website for any purpose.</p>

        <h3>Professional Advice</h3>

        <p>Any reliance you place on such information is therefore strictly at your own risk. It shall be your own responsibility to ensure that any products, services or information available through this website meet your specific requirements.</p>

        <p>This website contains material which is owned by or licensed to us. This material includes, but is not limited to, the design, layout, look, appearance and graphics. You may not reproduce, distribute, display or create derivative works of this website or any part thereof without our prior written consent.</p>

        <h3>External Links</h3>

        <p>Through this website you may be able to link to other websites which are not under the control of {company['name']}. We have no control over the nature, content and availability of those sites. The inclusion of any links does not necessarily imply a recommendation or endorse the views expressed within them.</p>

        <p>Every effort is made to keep the website up and running smoothly. However, {company['name']} takes no responsibility for, and will not be liable for, the website being temporarily unavailable due to technical issues beyond our control.</p>

        <h3>Limitation of Liability</h3>

        <p>In no event will we be liable for any loss or damage including without limitation, indirect or consequential loss or damage, or any loss or damage whatsoever arising from loss of data or profits arising out of, or in connection with, the use of this website.</p>

        <p>Through this website you may be able to link to other websites which are not under the control of {company['name']}. We have no control over the nature, content and availability of those sites. The inclusion of any links does not necessarily imply a recommendation or endorse the views expressed within them.</p>

        <h3>Solar Installation Services</h3>

        <p>Our solar installation services are provided with the highest standards of quality and safety. However, all solar installations carry inherent risks. We recommend consulting with qualified professionals and obtaining all necessary permits before proceeding with any solar installation project.</p>

        <p>{company['name']} shall not be liable for any damages arising from improper installation, misuse, or unauthorized modifications to solar systems installed by our technicians.</p>

        <h3>Product Warranties</h3>

        <p>Product warranties are provided by the respective manufacturers. {company['name']} acts as a distributor and reseller of solar products. While we stand behind the quality of products we sell, warranty claims must be directed to the manufacturer as per their warranty terms.</p>

        <p>We endeavour to provide accurate product information, but specifications may change without notice. It is the customer's responsibility to verify product specifications before purchase.</p>

        <h3>Contact Information</h3>

        <p>If you have any questions about this disclaimer or need clarification:</p>

        <p><strong>{company['name']}</strong><br>
        Email: <a href="mailto:{company['email']}">{company['email']}</a><br>
        Phone: <a href="tel:{company['phone']}">{company['phone']}</a><br>
        Address: {company['address']}</p>

        <p><em>This disclaimer was last updated on {timezone.now().date()}</em></p>
        """

        doc, created = LegalDocument.objects.get_or_create(
            document_type='disclaimer',
            defaults={
                'title': 'Website Disclaimer',
                'content': content,
                'short_description': 'Important legal notices and limitations regarding our website and services.',
                'version': '1.0',
                'is_active': True,
                'effective_date': timezone.now().date(),
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Created Disclaimer document')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Disclaimer document already exists')
            )

    def create_refund_policy_document(self):
        """Create the Refund Policy document"""
        company = self.get_company_info()

        content = f"""
        <h2>Refund Policy</h2>

        <p>At {company['name']}, we strive to provide high-quality solar products and services. This refund policy outlines the circumstances under which refunds may be granted for purchases made through our website or physical showroom.</p>

        <h3>Product Returns and Refunds</h3>

        <h4>Physical Products</h4>
        <ul>
            <li><strong>Return Window:</strong> Physical products may be returned within 30 days of purchase for a full refund</li>
            <li><strong>Condition Requirements:</strong> Items must be unused, in original packaging, and in resalable condition</li>
            <li><strong>Return Shipping:</strong> Customers are responsible for return shipping costs unless the item is defective</li>
            <li><strong>Restocking Fee:</strong> A 10% restocking fee may apply for certain items</li>
        </ul>

        <h4>Custom or Modified Products</h4>
        <ul>
            <li>Custom-sized solar panels and specially configured systems are not eligible for return unless defective</li>
            <li>Modified or installed products are not eligible for return</li>
        </ul>

        <h3>Service Refunds</h3>

        <h4>Solar Installation Services</h4>
        <ul>
            <li><strong>Cancellation Before Work Begins:</strong> Full refund if cancelled at least 48 hours before scheduled installation</li>
            <li><strong>Cancellation After Work Begins:</strong> Pro-rated refund based on work completed</li>
            <li><strong>Unsatisfactory Work:</strong> Refunds available if work doesn't meet agreed specifications</li>
        </ul>

        <h4>Maintenance Services</h4>
        <ul>
            <li>Service contracts are non-refundable once the service period has begun</li>
            <li>One-time maintenance services may be refunded if not performed within 30 days of purchase</li>
        </ul>

        <h3>Defective Products</h3>

        <ul>
            <li>All defective products are eligible for replacement or full refund within the manufacturer's warranty period</li>
            <li>Customers must provide proof of purchase and documentation of the defect</li>
            <li>Defective items will be repaired, replaced, or refunded at our discretion</li>
        </ul>

        <h3>How to Request a Refund</h3>

        <h4>Step 1: Contact Us</h4>
        <p>Send an email to <a href="mailto:{company['email']}">{company['email']}</a> or call us at <a href="tel:{company['phone']}">{company['phone']}</a> with your refund request.</p>

        <h4>Step 2: Provide Information</h4>
        <p>Include the following in your refund request:</p>
        <ul>
            <li>Order number or receipt</li>
            <li>Reason for the refund request</li>
            <li>Preferred refund method (bank transfer, M-Pesa, etc.)</li>
            <li>Photos or documentation (if applicable)</li>
        </ul>

        <h4>Step 3: Return Process</h4>
        <p>If your refund is approved:</p>
        <ul>
            <li>We'll provide a return authorization and shipping label</li>
            <li>Return the item within 7 days of receiving authorization</li>
            <li>Once the item is received and inspected, your refund will be processed</li>
        </ul>

        <h3>Refund Processing Time</h3>

        <ul>
            <li><strong>Bank Transfer:</strong> 5-7 business days after approval</li>
            <li><strong>M-Pesa:</strong> 1-2 business days after approval</li>
            <li><strong>Credit Card:</strong> 3-5 business days after approval (may take up to 2 billing cycles to appear on statement)</li>
        </ul>

        <h3>Refund Exceptions</h3>

        <p>The following items are not eligible for refunds:</p>
        <ul>
            <li>Products damaged by misuse or neglect</li>
            <li>Products with removed or damaged serial numbers</li>
            <li>Products purchased during clearance sales (unless defective)</li>
            <li>Digital products or software licenses (unless defective)</li>
            <li>Services that have been fully performed or completed</li>
        </ul>

        <h3>Exchanges</h3>

        <p>We offer exchanges for products of equal or greater value. If you wish to exchange an item:</p>
        <ul>
            <li>The item must be returned within 30 days</li>
            <li>The item must be unused and in original condition</li>
            <li>Price differences will be charged or credited accordingly</li>
        </ul>

        <h3>Contact Information</h3>

        <p>For refund requests or questions about this policy:</p>

        <p><strong>Customer Service</strong><br>
        {company['name']}<br>
        Email: <a href="mailto:{company['email']}">{company['email']}</a><br>
        Phone: <a href="tel:{company['phone']}">{company['phone']}</a><br>
        Address: {company['address']}</p>

        <p><em>This refund policy was last updated on {timezone.now().date()}</em></p>
        """

        doc, created = LegalDocument.objects.get_or_create(
            document_type='refund_policy',
            defaults={
                'title': 'Refund Policy',
                'content': content,
                'short_description': 'Learn about our refund policy for products and services.',
                'version': '1.0',
                'is_active': True,
                'effective_date': timezone.now().date(),
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Created Refund Policy document')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Refund Policy document already exists')
            )
