# Olivian Group - Django Project Documentation

## Project Overview
The Olivian Group Limited - Professional Solar Solutions Platform

This is a comprehensive Django-based business management system for a solar energy company in Kenya. It's designed for both B2B operations and customer-facing services, with a focus on complete quote-to-cash workflows, project management, and inventory control.

## System Architecture

### **Major Apps & Functionality:**

**🏗️ Core App (apps.core):**
- Company settings management (branding, colors, social media, business stats)
- Contact form handling with newsletter subscriptions
- Audit logging and activity tracking system
- User notifications with email integration
- Legal documents management (privacy policy, terms of service, cookie policy)
- Cookie consent and GDPR compliance
- System maintenance & admin features (backups, health checks, reports, API endpoints)

**👥 Accounts App (apps.accounts):**
- Custom User model with 10 distinct roles (super_admin, director, manager, sales_manager, sales_person, project_manager, inventory_manager, cashier, technician, customer)
- Automated employee ID generation (OG/ADM/001, OG/SPN/001, etc.)
- Email or username login capability
- User profiles with preferences and timezone settings
- Privacy consent tracking and language preferences
- Role-based permission system

**📦 Products App (apps.products):**
- Hierarchical product categories using MPTT for tree structure
- Comprehensive solar product specifications (power rating, efficiency, voltage, certifications)
- Multi-pricing support (cost, selling, sale prices) with promotional capabilities
- Inventory integration with low-stock thresholds and backorders
- Document management (installation manuals, datasheets up to 10MB)
- Rich media support (multiple product images, primary image assignment)
- Customer visibility controls and inquiry-only products
- Tag system and product reviews

**💰 Quotations App (apps.quotations):**
- Automated quotation numbering (OG-QUO-2024-0001 format)
- Customer management with integrated loyalty program (points, tiers: Bronze/Silver/Gold/Platinum)
- Advanced solar system calculations (ROI, payback periods, estimated savings)
- Multi-system types (Grid-tied, Off-grid, Hybrid, Backup systems)
- VAT handling (16% Kenya rate), discounts, financing options
- Template system for common solar configurations
- Web-based quotation request forms with status tracking
- Follow-up management and email automation

**🌞 Projects App (apps.projects):**
- Full project lifecycle management (PRJ-YYYY-0001 numbering)
- Task management with dependencies and assignments
- Budget integration with expense tracking
- Installation complexity rating system
- Progress tracking with photo uploads and status updates
- Customer communication and timeline management

**🔒 Budget App (apps.budget):**
- Department/project budget planning and monitoring
- Expense request approval workflows
- Budget category breakdowns and variance tracking
- Payment schedule management
- Financial compliance and audit trails

**🛒 Ecommerce App (apps.ecommerce):**
- Shopping cart and checkout process
- M-Pesa payment integration
- Order management and tracking
- Receipt generation and email delivery
- Customer order history and status updates

**📦 Inventory App (apps.inventory):**
- Multi-warehouse stock management
- Barcode/QR code generation and scanning
- Purchase order processing
- Stock movement tracking
- Supplier management integration
- Inventory synchronization with product catalog

### **Additional Apps:**
- **CRM**: Customer relationship management
- **POS**: Point of sale operations
- **Procurement**: Vendor and supplier management
- **Financial**: Advanced accounting features
- **Blog**: Content management system
- **Chat**: Real-time communication system

## Quick Setup Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py

# Alternative manual setup:
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver
```

### After Database Import (MySQL Production Data)
```bash
# After importing MySQL database, run this to fix context issues:
python manage.py setup_after_import

# Or run individual commands:
python manage.py migrate
python manage.py ensure_company_settings
python manage.py collectstatic --noinput
```

### Production Deployment (Shared Hosting)
```bash
# Install packages
pip install -r requirements.txt --user

# Set up database
python manage.py migrate --settings=olivian_solar.settings

# Collect static files
python manage.py collectstatic --noinput --settings=olivian_solar.settings
```

## Technical Implementation

### **Django Features Used:**
- Django 5.1.5 with Channels for WebSocket support
- Custom user model with role-based permissions
- MPTT for hierarchical product categories
- Django REST Framework for API endpoints
- WhiteNoise for static file serving
- Crispy Forms with Bootstrap 5
- CKEditor for rich text content
- Import/Export functionality
- Django Filters and Tagging
- Email templating with SendGrid/Mailgun integration

### **Security & Compliance:**
- CSRF protection and secure authentication
- Role-based access control with granular permissions
- Audit logging on all critical operations
- Cookie consent and GDPR compliance features
- Data validation and sanitization
- HTTPS enforcement in production

### **Kenya-Specific Business Features:**
- M-Pesa payment gateway integration
- KES currency formatting throughout
- 16% VAT rate calculations
- Nairobi timezone (Africa/Nairobi)
- Local business hour configurations

### **Modern Web Features:**
- Progressive Web App (PWA) support with service workers
- Responsive Bootstrap 5 design
- Offline functionality
- Real-time chat capabilities
- SEO optimization and meta tags
- Mobile-optimized interfaces

## Configuration

### Environment Variables (.env)
```bash
# Security
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database (Production MySQL, Development SQLite)
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

# Email Configuration
EMAIL_PROVIDER=sendgrid  # sendgrid, mailgun, smtp, console
SENDGRID_API_KEY=your-sendgrid-key
MAILGUN_SMTP_LOGIN=username
MAILGUN_SMTP_PASSWORD=password
```

### Key Model Relationships

**Business Workflow:**
1. **Lead Generation** → CRM app captures customer inquiries
2. **Quotation Creation** → Sales create detailed solar proposals
3. **Order Conversion** → Quotations convert to confirmed orders
4. **Project Setup** → Installation projects with task tracking
5. **Inventory Management** → Stock allocation and tracking
6. **Payment Processing** → M-Pesa integration
7. **Customer Updates** → Notifications and project status

## API & Integrations

- **REST API** at `/api/` with token authentication
- **M-Pesa Integration** for Kenyan payments
- **Email Services** (SendGrid/Mailgun/SMTP)
- **Cloud Storage** (AWS S3/Google Cloud)
- **Social Media** integration points
- **WhatsApp** business messaging

## Testing & Quality Assurance
```bash
# Run tests
python manage.py test

# Check for issues
python manage.py check

# Validate models
python manage.py validate

# Code quality
python manage.py flake8  # if configured
```

## System Health Monitoring

- **Performance Metrics**: CPU, memory, disk usage tracking
- **Database Health**: Connection monitoring and query performance
- **Backup System**: Automated database and media file backups
- **Activity Logging**: Comprehensive user action auditing
- **Error Handling**: Detailed error logging and reporting
- **Security Monitoring**: Failed login attempts and suspicious activity

## Roadmap & Future Development

The system has a planned 18-month roadmap expansion including:
- Point of Sale (POS) system
- Field service management
- Manufacturing module
- Business intelligence dashboard
- IoT device monitoring
- Quality management system
- Enterprise-level customization

## Development Best Practices

1. **Code Organization**: Clear app separation with proper naming
2. **Database Design**: Normalized schemas with appropriate indexes
3. **Security**: Input validation, authentication, authorization
4. **Performance**: Efficient queries, caching, optimization
5. **Scalability**: Modular design for feature expansion
6. **Testing**: Comprehensive test coverage
7. **Documentation**: Clear code comments and technical docs

## Support & Contact
- **Company**: The Olivian Group Limited
- **Website**: https://olivian.co.ke
- **Admin Panel**: https://olivian.co.ke/admin/
- **Email**: info@oliviangroup.com
- **Phone**: +254-700-000-000

---

## **COOKIE CONSENT FIX (Recently Implemented)**

### **Problem Fixed**
- Cookie policy banner was displaying repeatedly on every website visit
- Anonymous users experienced intrusive banner behavior due to unreliable consent tracking

### **Root Cause**
- Used IP address + User Agent hash for consent tracking, causing banner to show every time identifiers changed
- No persistent localStorage preference for anonymous users
- No consent expiry mechanism

### **Solution Implemented**
- **LocalStorage-first approach**: Anonymous users' consent stored in browser localStorage as primary storage
- **30-day consent expiry**: Consent remembered for 30 days to reduce intrusive prompts
- **Smart banner logic**: Banner only shows for genuine new visitors, not existing users with valid consent
- **Improved API handling**: Better fallback when server API calls fail
- **Rate limiting**: Banner won't show more than once per hour for existing users

### **Technical Changes**
- **Updated `cookie_manager.js`**: New dual-layer consent checking
- **Version cache-busting**: Updated JavaScript version from v3 to v31
- **Backward compatibility**: Maintains all existing functionality for logged-in users

## **CACHING OPTIMIZATION COMPLETED (Recent Fix)**

### **Problem Fixed**
- Website was serving cached content instead of live content, requiring hard refreshes
- Django page caching middleware was conflicting with PWA's offline-first strategy

### **Solution Implemented**
- **Removed Django Page Caching**: Eliminated `CACHE_MIDDLEWARE_SECONDS = 3600` and caching middleware
- **Added Smart Cache Control**: New `CacheControlMiddleware` adds proper no-cache headers for HTML pages while allowing static asset caching
- **Preserved PWA Offline Capability**: Service worker still provides offline caching when network is unavailable

### **Behavior Changes**
- ✅ **Pages load live** from server on every visit
- ✅ **No more hard refresh required** to see site updates
- ✅ **Offline mode still works** - cached pages serve when network fails
- ✅ **Static assets cached** appropriately for performance
- ✅ **Service worker updated** to v1.0.3 for cache busting

### **Technical Implementation**
```python
# Removed from settings.py:
# CACHE_MIDDLEWARE_SECONDS = 3600
# UpdateCacheMiddleware, FetchFromCacheMiddleware

# Added CacheControlMiddleware with:
# - no-cache headers for HTML pages
# - Appropriate caching for static assets
# - Preserved admin and API functionality
```

---

**Technical Summary**: Production-ready Django enterprise system built specifically for solar energy business operations in Kenya, featuring modern web technologies, comprehensive business logic, local market compliance, smart cookie consent system, and optimized caching for live-first, offline-capable web experience.
