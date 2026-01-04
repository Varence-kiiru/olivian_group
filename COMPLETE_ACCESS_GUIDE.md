# 🌟 Olivian Group - Complete System Access Guide

## 📁 **Template Structure Explained**

### **Current Template Organization:**

```
templates/
├── website/           # 🌐 PUBLIC WEBSITE (Customer-facing)
│   ├── base.html     # Modern website base template
│   ├── home.html     # Homepage with hero sections
│   ├── about.html    # About us page
│   ├── contact.html  # Contact page with forms
│   ├── services.html # Services description
│   └── products.html # Product showcase
│
├── dashboard/         # 🔐 MANAGEMENT SYSTEM (Staff/Admin)
│   └── base.html     # Professional admin interface
│
├── accounts/          # 👤 USER AUTHENTICATION
│   ├── login.html    # Login page
│   ├── register.html # Registration page
│   ├── dashboard.html # User dashboard
│   └── profile.html  # Profile management
│
├── products/          # 📦 PRODUCT MANAGEMENT
│   ├── product_list.html   # Product listing with filters
│   └── product_detail.html # Detailed product view
│
├── quotations/        # 💰 QUOTATION SYSTEM
│   └── solar_calculator.html # Multi-step calculator
│
├── ecommerce/         # 🛒 E-COMMERCE
│   └── cart.html     # Shopping cart
│
├── emails/            # 📧 EMAIL TEMPLATES
│   ├── base_email.html
│   ├── welcome.html
│   ├── quotation_created.html
│   └── order_confirmation.html
│
├── 404.html          # ⚠️ ERROR PAGES
└── 500.html
```

### **Template Purpose:**

**🌐 `website/`** - **Customer Experience**
- Modern, responsive design for public visitors
- Marketing-focused with strong branding
- Product browsing and information

**🔐 `dashboard/`** - **Business Management**  
- Professional interface for staff and admins
- Role-based navigation and functionality
- Data management and operations

---

## 🚀 **Complete Access Guide for All Users**

### **👥 USER TYPES & ACCESS LEVELS**

## 1. 🌍 **PUBLIC VISITORS (No Account)**

### **What They Can Access:**
- ✅ Browse the website
- ✅ View products and services
- ✅ Use solar calculator
- ✅ Contact forms
- ✅ View projects showcase

### **Access URLs:**
```
🏠 Homepage: https://olivian.co.ke/
📖 About Us: https://olivian.co.ke/about/
📞 Contact: https://olivian.co.ke/contact/
🔧 Services: https://olivian.co.ke/services/
📦 Products: https://olivian.co.ke/products/
🧮 Calculator: https://olivian.co.ke/quotations/calculator/
🏗️ Projects: https://olivian.co.ke/projects/
```

### **How to Get Started:**
1. **Visit the website**: `https://olivian.co.ke/`
2. **Browse products**: Click "Products" in navigation
3. **Get a quote**: Use "Solar Calculator" 
4. **Contact us**: Fill contact form for inquiries

---

## 2. 👤 **CUSTOMERS (Registered Users)**

### **Registration Process:**
1. **Go to**: `https://olivian.co.ke/accounts/register/`
2. **Fill the form** with personal details
3. **Select "Customer"** as account type
4. **Verify email** (if email verification is enabled)
5. **Login**: `https://olivian.co.ke/accounts/login/`

### **What They Can Access:**
- ✅ Everything public visitors can access
- ✅ Personal dashboard
- ✅ Order history and tracking
- ✅ Quotation management
- ✅ Profile settings
- ✅ Shopping cart and checkout

### **Customer Dashboard URLs:**
```
🏠 Dashboard: https://olivian.co.ke/accounts/dashboard/
👤 Profile: https://olivian.co.ke/accounts/profile/
🛒 Cart: https://olivian.co.ke/shop/cart/
📋 Orders: https://olivian.co.ke/shop/orders/
💰 Quotations: https://olivian.co.ke/quotations/my-quotes/
```

### **How Customers Use the System:**
1. **Login** to access personal dashboard
2. **Browse and add products** to cart
3. **Request quotes** through calculator
4. **Track orders** and project progress
5. **Manage profile** and preferences

---

## 3. 👨‍💼 **SALES TEAM (Sales Person/Manager)**

### **Account Setup:**
- **Created by Admin** in Django Admin
- **Role**: Sales Person or Sales Manager
- **Access**: Sales-focused dashboard

### **What They Can Access:**
- ✅ Customer quotations and management
- ✅ Order processing and tracking  
- ✅ Customer communication
- ✅ Product catalog management
- ✅ Sales reporting

### **Sales Dashboard URLs:**
```
🏠 Dashboard: https://olivian.co.ke/accounts/dashboard/
💰 Quotations: https://olivian.co.ke/quotations/
🛒 Orders: https://olivian.co.ke/shop/orders/
🧾 Receipts: https://olivian.co.ke/shop/receipts/
📊 Reports: https://olivian.co.ke/reports/sales/
```

### **Daily Workflow:**
1. **Login** to sales dashboard
2. **Review new quotation requests**
3. **Process customer orders**
4. **Generate and send quotes**
5. **Follow up on pending orders**

---

## 4. 🏗️ **PROJECT MANAGERS**

### **Account Setup:**
- **Created by Admin** with Project Manager role
- **Access**: Project and budget management

### **What They Can Access:**
- ✅ Project management and tracking
- ✅ Budget planning and monitoring
- ✅ Resource allocation
- ✅ Installation scheduling
- ✅ Project reporting

### **Project Management URLs:**
```
🏠 Dashboard: https://olivian.co.ke/accounts/dashboard/
🏗️ Projects: https://olivian.co.ke/projects/
💵 Budget: https://olivian.co.ke/budget/
📅 Schedule: https://olivian.co.ke/projects/schedule/
📊 Reports: https://olivian.co.ke/reports/projects/
```

### **Daily Workflow:**
1. **Review active projects**
2. **Update project progress**
3. **Manage budgets and expenses**
4. **Coordinate with installation teams**
5. **Generate project reports**

---

## 5. 📦 **INVENTORY MANAGERS**

### **Account Setup:**
- **Created by Admin** with Inventory Manager role
- **Access**: Product and stock management

### **What They Can Access:**
- ✅ Product catalog management
- ✅ Stock level monitoring
- ✅ Purchase order management
- ✅ Supplier coordination
- ✅ Inventory reporting

### **Inventory Management URLs:**
```
🏠 Dashboard: https://olivian.co.ke/accounts/dashboard/
📦 Products: https://olivian.co.ke/products/
📊 Inventory: https://olivian.co.ke/inventory/
🛒 Purchase Orders: https://olivian.co.ke/inventory/purchase-orders/
📈 Stock Reports: https://olivian.co.ke/reports/inventory/
```

### **Daily Workflow:**
1. **Monitor stock levels**
2. **Update product information**
3. **Process purchase orders**
4. **Manage supplier relationships**
5. **Generate inventory reports**

---

## 6. 👨‍💼 **MANAGERS & ADMINS**

### **Account Setup:**
- **Super Admin**: Full system access
- **Manager**: Department oversight access

### **What They Can Access:**
- ✅ **Complete system overview**
- ✅ **All departmental dashboards**
- ✅ **User management**
- ✅ **System configuration**
- ✅ **Advanced reporting**

### **Management URLs:**
```
🏠 Dashboard: https://olivian.co.ke/accounts/dashboard/
👥 User Management: https://olivian.co.ke/accounts/users/
⚙️ System Admin: https://olivian.co.ke/admin/
🏢 Company Settings: https://olivian.co.ke/admin/core/companysettings/
🏦 Bank Accounts: https://olivian.co.ke/admin/core/bankaccount/
📊 Analytics: https://olivian.co.ke/reports/
```

### **Management Workflow:**
1. **Monitor overall system performance**
2. **Manage user accounts and permissions**
3. **Configure system settings**
4. **Review departmental reports**
5. **Make strategic decisions**

---

## 🔐 **DJANGO ADMIN ACCESS (Super Users Only)**

### **Who Can Access:**
- **Super Admins** only
- **System Administrators**

### **Access URL:**
```
⚙️ Django Admin: https://olivian.co.ke/admin/
```

### **What's Available in Admin:**
- **👥 User Management** - Create/edit users and roles
- **🏢 Company Settings** - Configure company details and M-Pesa
- **🏦 Bank Accounts** - Manage multiple bank accounts  
- **📦 Product Management** - Add/edit products and categories
- **💰 Financial Settings** - VAT rates, currencies
- **📧 Email Configuration** - SMTP settings
- **🔧 System Configuration** - Advanced settings

### **Admin Workflow:**
1. **Login** with superuser credentials
2. **Configure company settings** (first-time setup)
3. **Create user accounts** for staff
4. **Set up bank accounts** and M-Pesa details
5. **Configure products** and categories
6. **Monitor system health**

---

## 📱 **MOBILE ACCESS**

### **All User Types:**
- ✅ **Fully responsive** on mobile devices
- ✅ **Touch-friendly** navigation
- ✅ **Mobile-optimized** forms and interfaces

### **Mobile URLs:** 
*Same as desktop, automatically adapts*

---

## 🔑 **QUICK START GUIDE**

### **For New Customers:**
1. **Visit**: `https://olivian.co.ke/`
2. **Register**: Click "Get Started" → Fill registration form
3. **Login**: Use credentials to access dashboard
4. **Browse**: Explore products and use solar calculator

### **For New Staff:**
1. **Contact Admin** to create account with appropriate role
2. **Receive login credentials** via email
3. **Login**: `https://olivian.co.ke/accounts/login/`
4. **Access dashboard** based on assigned role

### **For System Setup:**
1. **Admin Login**: `https://olivian.co.ke/admin/`
2. **Configure Company**: Core → Company Settings
3. **Add Bank Accounts**: Core → Bank Accounts  
4. **Create Users**: Authentication → Users
5. **Add Products**: Products → Products

---

## 🎯 **USER JOURNEY EXAMPLES**

### **Customer Journey:**
```
Website → Browse Products → Use Calculator → Register → 
Get Quote → Review → Place Order → Track Progress → 
Receive Installation → Post-Sale Support
```

### **Sales Journey:**
```
Login → Review Leads → Create Quotes → Follow Up → 
Process Orders → Coordinate Installation → 
Generate Invoices → Customer Support
```

### **Project Journey:**
```
Login → Assign Projects → Plan Resources → Track Progress → 
Manage Budget → Coordinate Teams → Quality Control → 
Project Completion → Reporting
```

---

## 📞 **SUPPORT & HELP**

### **For Customers:**
- **Website Support**: Use contact form at `/contact/`
- **Phone**: {{ company.phone|default:"+254-719-728-666" }}
- **Email**: info@olivian.co.ke

### **For Staff:**
- **System Issues**: Contact IT Admin
- **Login Problems**: admin@olivian.co.ke  
- **Training**: Request from Manager

---

## ✅ **SYSTEM STATUS SUMMARY**

**🌐 Public Website**: Fully functional with modern design  
**🔐 Management System**: Complete role-based access  
**👤 User Authentication**: Registration and login working  
**📦 Product Management**: Catalog and inventory ready  
**💰 Quotation System**: Calculator and processing active  
**🛒 E-commerce**: Cart and checkout functional  
**📧 Email System**: Automated notifications enabled  
**📱 Mobile Support**: Fully responsive across devices  

**🎉 THE SYSTEM IS READY FOR PRODUCTION USE! 🎉**
