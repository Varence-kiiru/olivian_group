from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.quotations.models import Quotation, Customer
import json

User = get_user_model()

class CalculatorFeatureTestCase(TestCase):
    """Test new calculator features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@olivian.co.ke',
            password='testpass123',
            role='sales_person'
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@test.com',
            phone='+254700000000',
            address='Test Address',
            city='Nairobi',
            monthly_consumption=300.00,
            average_monthly_bill=5000.00,
            roof_area=100.00
        )
        self.quotation = Quotation.objects.create(
            customer=self.customer,
            quotation_type='custom_solution',
            system_type='grid_tied',
            system_capacity=5.0,
            estimated_generation=600.00,
            estimated_monthly_savings=3000.00,
            estimated_annual_savings=36000.00,
            payback_period_months=120,
            roi_percentage=15.00,
            valid_until=timezone.now().date() + timezone.timedelta(days=30),
            total_amount=500000.00,
            salesperson=self.user
        )
    
    def test_calculator_page_loads(self):
        """Test that calculator page loads correctly"""
        response = self.client.get(reverse('quotations:calculator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Solar System Calculator')
    
    def test_quotation_pdf_view_requires_login(self):
        """Test that PDF view requires authentication"""
        response = self.client.get(
            reverse('quotations:pdf', args=[self.quotation.quotation_number])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_quotation_pdf_view_authenticated(self):
        """Test PDF generation with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('quotations:pdf', args=[self.quotation.quotation_number])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
    
    def test_generate_quotation_from_calculator(self):
        """Test quotation generation from calculator"""
        data = {
            'calculatorData': {
                'capacity': 5.0,
                'systemType': 'grid_tied',
                'propertyType': 'residential',
                'totalSystemCost': 500000.00,
                'monthlyConsumption': 300,
                'location': 'nairobi'
            },
            'customerData': {
                'name': 'New Customer',
                'email': 'new@customer.com',
                'phone': '+254700000001'
            }
        }
        
        response = self.client.post(
            reverse('quotations:generate_quotation'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('quotation_number', response_data)
    
    def test_schedule_consultation(self):
        """Test consultation scheduling"""
        data = {
            'customerData': {
                'name': 'Consultation Customer',
                'email': 'consult@customer.com',
                'phone': '+254700000002'
            },
            'consultationData': {
                'preferredDate': '2024-12-31',
                'preferredTime': 'morning',
                'consultationType': 'site_visit'
            }
        }
        
        response = self.client.post(
            reverse('quotations:schedule_consultation'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('successfully', response_data['message'])

class QuotationPDFTestCase(TestCase):
    """Test PDF generation functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='pdftest',
            email='pdf@olivian.co.ke',
            password='testpass123',
            role='sales_manager'
        )
        self.customer = Customer.objects.create(
            name='PDF Test Customer',
            email='pdf@customer.com',
            phone='+254700000003',
            address='PDF Test Address',
            city='Nairobi',
            monthly_consumption=500.00,
            average_monthly_bill=8000.00,
            roof_area=150.00
        )
        self.quotation = Quotation.objects.create(
            customer=self.customer,
            quotation_type='custom_solution',
            system_type='hybrid',
            system_capacity=10.0,
            estimated_generation=1200.00,
            estimated_monthly_savings=6000.00,
            estimated_annual_savings=72000.00,
            payback_period_months=100,
            roi_percentage=20.00,
            valid_until=timezone.now().date() + timezone.timedelta(days=30),
            total_amount=1000000.00,
            salesperson=self.user
        )
    
    def test_pdf_content_includes_company_branding(self):
        """Test that PDF includes company branding"""
        self.client.login(username='pdftest', password='testpass123')
        response = self.client.get(
            reverse('quotations:pdf', args=[self.quotation.quotation_number])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('quotation_', response['Content-Disposition'])
    
    def test_pdf_permission_check(self):
        """Test PDF access permissions"""
        # Create another user who shouldn't have access
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@olivian.co.ke',
            password='testpass123',
            role='sales_person'
        )
        
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('quotations:pdf', args=[self.quotation.quotation_number])
        )
        
        # Should redirect due to permission check
        self.assertEqual(response.status_code, 302)
