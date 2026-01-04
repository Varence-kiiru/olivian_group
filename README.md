# Olivian Group - Professional Solar Solutions Platform

A comprehensive Django-based website for The Olivian Group Limited, featuring product catalogs, quotation systems, project management, inventory control, and budget management.

## 🚀 Quick Start

### Development Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Database (Development)**
   ```bash
   python manage.py migrate --settings=olivian_solar.settings_dev
   ```

3. **Create Demo Data**
   ```bash
   python manage.py setup_demo --settings=olivian_solar.settings_dev
   ```

4. **Run Development Server**
   ```bash
   python manage.py runserver --settings=olivian_solar.settings_dev
   ```

5. **Access the Application**
   - Website: https://olivian.co.ke/
   - Admin Panel: https://olivian.co.ke/admin/
   - Admin Login: `admin` / `admin123`

### Production Deployment

1. **Environment Configuration**
   - Copy `.env` and update with production values
   - Set `DEBUG=False`
   - Configure MySQL database
   - Add your domain to `ALLOWED_HOSTS`

2. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

3. **Web Server Configuration**
   - Configure Apache/Nginx to serve static files
   - Set up WSGI application
   - Enable HTTPS

## 🏗️ System Architecture

### Core Applications

- **`apps.accounts`** - User management with 9 role types
- **`apps.core`** - Company settings and base functionality
- **`apps.products`** - Solar product catalog with categories
- **`apps.quotations`** - Automated quotation system (QUO-YYYY-0001)
- **`apps.projects`** - Project management with budget tracking
- **`apps.budget`** - Budget management and expense approval
- **`apps.ecommerce`** - Shopping cart and order processing
- **`apps.inventory`** - Warehouse and stock management

### Key Features

✅ **Automatic Numbering System**
- Quotations: QUO-2024-0001
- Orders: ORD-2024-0001
- Projects: PRJ-2024-0001
- Purchase Orders: PO-2024-0001

✅ **Financial Integration**
- 16% VAT handling (Kenya)
- Kenyan Shilling (KES) formatting
- Budget system integration
- Quote-to-sale conversion

✅ **Role-Based Access Control**
- Super Admin, Manager, Sales Manager
- Sales Person, Project Manager
- Inventory Manager, Cashier
- Customer, Technician

✅ **Solar Industry Specific**
- Power ratings, efficiency percentages
- System types (Grid-tied, Off-grid, Hybrid)
- Installation complexity tracking
- ROI and payback calculations

## 👥 User Roles & Permissions

| Role | Access Level | Key Features |
|------|-------------|-------------|
| **Super Admin** | Full System | All permissions, system configuration |
| **Manager** | Management | Reports, project oversight, staff management |
| **Sales Manager** | Sales + Reports | Quotation management, sales analytics |
| **Sales Person** | Sales Only | Create quotations, manage leads |
| **Project Manager** | Projects + Budget | Project tracking, task management |
| **Inventory Manager** | Inventory + POS | Stock management, purchase orders |
| **Cashier** | POS + Customers | Point of sale, customer management |
| **Customer** | Self-Service | View products, track orders/projects |
| **Technician** | Field Work | View projects, update tasks |

## 💾 Database Models

### Product Management
- **Product**: Solar panels, inverters, batteries with technical specs
- **ProductCategory**: MPTT hierarchical categories
- **ProductImage/Document**: Rich media support

### Quotation System
- **Quotation**: Automated numbering with conversion to sales
- **QuotationItem**: Line items with specifications
- **Customer**: Detailed customer information

### Project Management
- **Project**: Full project lifecycle tracking
- **ProjectTask**: Task management with dependencies
- **ProjectExpense**: Cost tracking and budget integration

### Budget Management
- **Budget**: Department/project budgets with approval workflow
- **ExpenseRequest**: Expense approval system
- **BudgetCategory**: Granular budget control

## 🎨 Frontend Features

### Design System
- **Primary Color**: #38b6ff (Olivian Blue)
- **Secondary Color**: #ffffff (White)
- **Framework**: Bootstrap 5
- **Icons**: Font Awesome 6
- **Responsive**: Mobile-first design

### User Experience
- Professional solar industry aesthetic
- Intuitive navigation with breadcrumbs
- Real-time cart updates
- Progressive web app ready
- Accessibility compliant (WCAG 2.1 AA)

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=olivian_solar
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost

# Company Information
COMPANY_NAME=The Olivian Group Limited
COMPANY_EMAIL=info@oliviangroup.com
COMPANY_PHONE=+254-700-000-000

# M-Pesa Integration
MPESA_CONSUMER_KEY=your-mpesa-key
MPESA_CONSUMER_SECRET=your-mpesa-secret
MPESA_SHORTCODE=174379
```

### Currency & Tax Settings
- **Default Currency**: KES (Kenyan Shillings)
- **VAT Rate**: 16% (Kenya standard)
- **Timezone**: Africa/Nairobi

## 📱 API Endpoints

The system includes RESTful APIs for:
- Product catalog
- Quotation management
- Project tracking
- Inventory updates
- Order processing

API documentation available at `/api/` with token authentication.

## 🔒 Security Features

- CSRF protection
- Role-based access control
- Audit logging for critical operations
- Data encryption for sensitive information
- Rate limiting on API endpoints
- Secure file upload validation

## 🚀 Deployment Guide

### Shared Hosting (cPanel)

1. **Upload Files**
   ```bash
   # Upload project files to public_html
   # Ensure .env file is properly configured
   ```

2. **Python Environment**
   ```bash
   pip install -r requirements.txt --user
   ```

3. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. **Web Server Configuration**
   - Set document root to project directory
   - Configure WSGI application
   - Enable SSL certificate

### VPS/Dedicated Server

1. **System Requirements**
   - Python 3.8+
   - MySQL 8.0+
   - Nginx/Apache
   - SSL certificate

2. **Installation**
   ```bash
   # Clone repository
   git clone <repository-url>
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your settings
   
   # Set up database
   python manage.py migrate
   python manage.py collectstatic
   
   # Create superuser
   python manage.py createsuperuser
   ```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Code Quality
```bash
python manage.py check
python manage.py validate
```

### Demo Data
```bash
python manage.py setup_demo --settings=olivian_solar.settings_dev
```

## 📞 Support & Contact

- **Company**: The Olivian Group Limited
- **Website**: https://oliviangroup.com
- **Email**: info@oliviangroup.com
- **Phone**: +254-700-000-000

## 📄 License

Proprietary software for The Olivian Group Limited.

---

*Built with Django 5.1+ for the solar energy industry in Kenya* 🌟
