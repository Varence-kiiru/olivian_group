# Dynamic Contact Management System

## Overview
The Olivian Group system has been enhanced to eliminate hardcoded contact information and replace it with a dynamic, admin-configurable contact management system.

## What Was Changed

### 1. Enhanced CompanySettings Model
**File:** `apps/core/models.py`

**New Fields Added:**
- `sales_phone` - Sales department phone number
- `sales_email` - Sales department email
- `support_phone` - Support phone number  
- `support_email` - Support email
- `whatsapp_number` - WhatsApp business number
- `business_hours_weekday` - Weekday business hours
- `business_hours_saturday` - Saturday business hours
- `business_hours_sunday` - Sunday business hours
- `showroom_hours_weekday` - Weekday showroom hours
- `showroom_hours_saturday` - Saturday showroom hours
- `showroom_hours_sunday` - Sunday showroom hours
- `facebook_url` - Facebook page URL
- `twitter_url` - Twitter profile URL
- `linkedin_url` - LinkedIn company page URL
- `instagram_url` - Instagram profile URL
- `youtube_url` - YouTube channel URL
- `google_maps_url` - Google Maps location URL
- `google_maps_embed_url` - Google Maps embed URL

**New Methods:**
- `get_settings()` - Singleton pattern to get company settings
- `get_whatsapp_url()` - Generate WhatsApp URL from phone number
- `get_social_media_links()` - Get all social media links as dictionary
- `has_social_media()` - Check if any social media links are configured

### 2. Enhanced Context Processor
**File:** `apps/core/context_processors.py`

**Improvements:**
- Uses singleton pattern for company settings
- Provides computed properties (whatsapp_url, social_media, has_social_media)
- Better error handling with comprehensive fallbacks
- Consistent data structure for templates

### 3. Updated Admin Interface
**File:** `apps/core/admin.py`

**New Admin Sections:**
- Contact Details
- Business Hours
- Showroom Hours  
- Social Media Links
- Location & Maps

### 4. Template Updates

#### Contact Page (`templates/website/contact.html`)
**Changes:**
- Dynamic phone numbers (main, sales, support)
- Dynamic email addresses (general, sales, support)
- Dynamic WhatsApp link
- Dynamic business hours
- Dynamic address and Google Maps integration
- Conditional display (only show if data exists)

#### Website Base Template (`templates/website/base.html`)
**Changes:**
- Dynamic social media links in footer
- Dynamic contact information in footer
- Dynamic company name throughout
- Conditional display of social media section
- Dynamic Google Maps integration

## Files Modified

### Core Files:
1. `apps/core/models.py` - Enhanced CompanySettings model
2. `apps/core/admin.py` - Enhanced admin interface
3. `apps/core/context_processors.py` - Improved context processor
4. `apps/core/migrations/0004_*.py` - Database migration

### Templates Updated:
1. `templates/website/contact.html` - All contact information now dynamic
2. `templates/website/base.html` - Footer contact and social media dynamic

### Management Commands:
1. `apps/core/management/commands/setup_company_settings.py` - Setup initial data

## Hardcoded Values Eliminated

### Phone Numbers:
- ❌ `+254-719-728-666` (Main)
- ❌ `+254-719-728-667` (Sales)  
- ❌ `+254-719-728-668` (Support)
- ✅ Now: `{{ company.phone }}`, `{{ company.sales_phone }}`, `{{ company.support_phone }}`

### Email Addresses:
- ❌ `info@olivian.co.ke`
- ❌ `sales@olivian.co.ke`
- ❌ `support@olivian.co.ke`
- ✅ Now: `{{ company.email }}`, `{{ company.sales_email }}`, `{{ company.support_email }}`

### Business Hours:
- ❌ `Mon - Fri: 8:00 AM - 6:00 PM`
- ❌ `Sat: 9:00 AM - 2:00 PM`
- ✅ Now: `{{ company.business_hours_weekday }}`, `{{ company.business_hours_saturday }}`

### Social Media:
- ❌ `<a href="#">` (Empty links)
- ✅ Now: `{% if social_media.facebook %}<a href="{{ social_media.facebook }}">{% endif %}`

### Addresses:
- ❌ `Westlands Office Park, Ring Road Parklands, Nairobi, Kenya`
- ✅ Now: `{{ company.address|linebreaks }}`

### WhatsApp:
- ❌ `https://wa.me/254719728666`
- ✅ Now: `{{ whatsapp_url }}`

## How to Use

### 1. Access Admin Interface
1. Go to Django Admin: `http://your-domain/admin/`
2. Navigate to **Core > Company Settings**
3. Click on the company settings entry (there should only be one)

### 2. Update Contact Information
- **Basic Information:** Company name, logo, address, main phone, email, website
- **Contact Details:** Sales phone/email, support phone/email, WhatsApp number
- **Business Hours:** Weekday, Saturday, Sunday hours for office and showroom
- **Social Media:** Facebook, Twitter, LinkedIn, Instagram, YouTube URLs
- **Location:** Google Maps URLs for directions and embedding

### 3. Template Usage Examples

#### Check if contact info exists:
```html
{% if company.sales_phone %}
    <a href="tel:{{ company.sales_phone }}">{{ company.sales_phone }}</a>
{% endif %}
```

#### WhatsApp integration:
```html
{% if whatsapp_url %}
    <a href="{{ whatsapp_url }}" target="_blank">{{ company.whatsapp_number }}</a>
{% endif %}
```

#### Social media links:
```html
{% if has_social_media %}
    <div class="social-links">
        {% if social_media.facebook %}<a href="{{ social_media.facebook }}">Facebook</a>{% endif %}
        {% if social_media.twitter %}<a href="{{ social_media.twitter }}">Twitter</a>{% endif %}
    </div>
{% endif %}
```

## Benefits

### 1. Admin Control
- ✅ Non-technical users can update contact information
- ✅ No need for developer intervention for contact changes
- ✅ Immediate updates across all pages

### 2. Consistency
- ✅ Single source of truth for all contact information
- ✅ Consistent formatting across the entire website
- ✅ No risk of outdated information on some pages

### 3. Flexibility
- ✅ Easy to add new contact methods
- ✅ Conditional display (hide sections if not configured)
- ✅ Support for multiple time zones and formats

### 4. Maintenance
- ✅ Eliminates the need to search through templates for hardcoded values
- ✅ Easier to maintain and update
- ✅ Version control friendly (no contact info in code)

## Setup Instructions

### 1. Apply Database Migration
```bash
python manage.py migrate core
```

### 2. Setup Initial Data
```bash
python manage.py setup_company_settings
```

### 3. Configure in Admin
1. Access Django Admin
2. Go to Core > Company Settings
3. Fill in all relevant contact information
4. Save changes

### 4. Verify Changes
1. Visit the contact page: `/contact/`
2. Check the footer on any page
3. Verify social media links appear (if configured)

## Future Enhancements

### Possible Additions:
1. **Multiple Locations:** Support for multiple office locations
2. **Operating Hours per Location:** Different hours for different locations  
3. **Holiday Hours:** Special hours for holidays
4. **Department-Specific Contact:** More granular contact information
5. **Localization:** Multi-language support for contact information
6. **Contact Form Integration:** Dynamic form recipient based on inquiry type

### Template Improvements:
1. **Structured Data:** Add JSON-LD structured data for better SEO
2. **vCard Integration:** Generate downloadable contact cards
3. **Click-to-Call:** Enhanced mobile experience
4. **Map Integration:** Embedded Google Maps on contact page

## Migration Notes

### For Developers:
- All templates now use `{{ company.field_name }}` instead of hardcoded values
- Context processor provides additional computed properties
- Admin interface has been reorganized for better UX
- Database migration adds new fields with sensible defaults

### For Content Managers:
- All contact information is now manageable through Django Admin
- Changes take effect immediately across the entire website
- No technical knowledge required for updates
- Social media links are optional and hidden if not configured

This enhancement makes the Olivian Group website much more maintainable and gives complete control over contact information to the admin users.
