from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import CompanySettings, Currency
from apps.products.models import ProductCategory, Product
from apps.quotations.models import Customer

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up demo data for Olivian Group'

    def handle(self, *args, **options):
        self.stdout.write("Setting up demo data for Olivian Group...")
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@oliviangroup.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='super_admin'
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user (admin/admin123)'))
        
        # Create company settings
        if not CompanySettings.objects.exists():
            CompanySettings.objects.create(
                name='The Olivian Group Limited',
                address='P.O. Box 12345, Nairobi, Kenya',
                phone='+254-700-000-000',
                email='info@oliviangroup.com',
                website='https://oliviangroup.com',
                primary_color='#38b6ff',
                secondary_color='#ffffff',
                default_currency='KES',
                vat_rate=16.0
            )
            self.stdout.write(self.style.SUCCESS('Created company settings'))
        
        # Create currencies
        if not Currency.objects.exists():
            currencies = [
                {'code': 'KES', 'name': 'Kenyan Shilling', 'symbol': 'KSh', 'exchange_rate': 1.0},
                {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'exchange_rate': 0.0073},
                {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'exchange_rate': 0.0067},
            ]
            for curr in currencies:
                Currency.objects.create(**curr)
            self.stdout.write(self.style.SUCCESS('Created currencies'))
        
        # Create product categories
        categories_data = [
            {'name': 'Solar Panels', 'description': 'Photovoltaic solar panels'},
            {'name': 'Inverters', 'description': 'Solar power inverters'},
            {'name': 'Batteries', 'description': 'Solar battery storage systems'},
            {'name': 'Mounting Systems', 'description': 'Solar panel mounting hardware'},
            {'name': 'Monitoring', 'description': 'Solar monitoring equipment'},
            {'name': 'Accessories', 'description': 'Cables, connectors, and other accessories'},
        ]
        
        for cat_data in categories_data:
            if not ProductCategory.objects.filter(name=cat_data['name']).exists():
                ProductCategory.objects.create(**cat_data)
        
        self.stdout.write(self.style.SUCCESS('Created product categories'))
        
        # Create sample products
        panel_category = ProductCategory.objects.get(name='Solar Panels')
        inverter_category = ProductCategory.objects.get(name='Inverters')
        
        products_data = [
            {
                'name': 'Monocrystalline Solar Panel 450W',
                'sku': 'SP-MONO-450',
                'category': panel_category,
                'product_type': 'solar_panel',
                'brand': 'SolarTech',
                'short_description': 'High-efficiency monocrystalline solar panel',
                'description': 'Premium monocrystalline solar panel with excellent performance',
                'power_rating': 450,
                'efficiency': 22.1,
                'voltage': '24V',
                'dimensions': '2100 x 1040 x 35 mm',
                'weight': 23.5,
                'warranty_years': 25,
                'cost_price': 18000,
                'selling_price': 25000,
                'quantity_in_stock': 50,
                'featured': True,
            },
            {
                'name': 'Solar Inverter 5kW MPPT',
                'sku': 'INV-MPPT-5K',
                'category': inverter_category,
                'product_type': 'inverter',
                'brand': 'PowerMax',
                'short_description': 'High-efficiency MPPT solar inverter',
                'description': 'Advanced MPPT solar inverter with monitoring capabilities',
                'power_rating': 5000,
                'efficiency': 97.5,
                'voltage': '48V',
                'dimensions': '430 x 310 x 145 mm',
                'weight': 15.2,
                'warranty_years': 5,
                'cost_price': 45000,
                'selling_price': 65000,
                'quantity_in_stock': 25,
                'featured': True,
            }
        ]
        
        for prod_data in products_data:
            if not Product.objects.filter(sku=prod_data['sku']).exists():
                Product.objects.create(**prod_data)
        
        self.stdout.write(self.style.SUCCESS('Created sample products'))
        
        # Create sample customer
        if not Customer.objects.filter(email='demo@customer.com').exists():
            Customer.objects.create(
                name='Demo Customer',
                email='demo@customer.com',
                phone='+254-700-123-456',
                address='Demo Address, Nairobi',
                city='Nairobi',
                country='Kenya',
                monthly_consumption=300,
                average_monthly_bill=8500,
                property_type='residential',
                roof_type='iron_sheets',
                roof_area=80
            )
            self.stdout.write(self.style.SUCCESS('Created sample customer'))
        
        # Create sample users
        user_roles = [
            ('sales', 'sales@oliviangroup.com', 'sales_person', 'Sales', 'Person'),
            ('manager', 'manager@oliviangroup.com', 'manager', 'Project', 'Manager'),
            ('customer', 'customer@demo.com', 'customer', 'Demo', 'Customer'),
        ]
        
        for username, email, role, first_name, last_name in user_roles:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=email,
                    password='demo123',
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
        
        self.stdout.write(self.style.SUCCESS('Created sample users'))
        self.stdout.write(self.style.SUCCESS('\nDemo data setup completed!'))
        self.stdout.write('Admin credentials: admin/admin123')
        self.stdout.write('Sample users: sales/demo123, manager/demo123, customer/demo123')
