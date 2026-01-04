from django.conf import settings
from .models import CompanySettings, KenyanHoliday, HolidayOffer

def company_info(request):
    """Add company information to template context"""
    # Define a safe company wrapper class
    class CompanyWrapper:
        def __init__(self, company_obj=None):
            if company_obj:
                # Copy all attributes from the original object
                for field in company_obj._meta.fields:
                    setattr(self, field.name, getattr(company_obj, field.name, None))

            # Ensure all template-required attributes exist with fallbacks
            self.name = getattr(self, 'name', 'The Olivian Group Limited')
            self.email = getattr(self, 'email', 'info@olivian.co.ke')
            self.phone = getattr(self, 'phone', '+254-719-728-666')
            self.address = getattr(self, 'address', 'Kahawa Sukari Road, Nairobi, Kenya')
            self.website = getattr(self, 'website', 'https://olivian.co.ke')

            # Company messaging
            self.tagline = getattr(self, 'tagline', 'Professional Solar Solutions')
            self.about_description = getattr(self, 'about_description', 'Professional solar solutions for homes and businesses in Kenya.')
            self.mission_statement = getattr(self, 'mission_statement', '')
            self.vision_statement = getattr(self, 'vision_statement', '')

            # SEO and Meta
            self.meta_description = getattr(self, 'meta_description', self.about_description)
            self.meta_keywords = getattr(self, 'meta_keywords', 'solar panels Kenya, solar installation, solar energy, renewable energy, solar power')

            # Branding and Media
            self.logo = getattr(self, 'logo', None)
            self.favicon = getattr(self, 'favicon', None)
            self.hero_image = getattr(self, 'hero_image', None)
            self.about_hero_image = getattr(self, 'about_hero_image', None)
            self.company_story_image = getattr(self, 'company_story_image', None)

            # Hero content
            self.hero_title = getattr(self, 'hero_title', "Save KES 150,000+ on Your First Year - Go Solar Today!")
            self.hero_subtitle = getattr(self, 'hero_subtitle', "Join 500+ Kenya families who cut electricity bills by 75% with professional solar installations. Complete system design, financing & installation - starts from KES 250,000.")
            self.hero_disclaimer = getattr(self, 'hero_disclaimer', "Professional site assessment and 10-year warranty included. Payback period: 3-5 years.")

            # Urgency banner
            self.urgency_banner_enabled = getattr(self, 'urgency_banner_enabled', True)
            self.urgency_banner_text = getattr(self, 'urgency_banner_text', "Limited Time: Get FREE installation assessment this month!")
            self.urgency_banner_end_date = getattr(self, 'urgency_banner_end_date', None)
            self.urgency_banner_subtitle = getattr(self, 'urgency_banner_subtitle', "Valid for the next 30 days. Don't miss this opportunity!")
            self.urgency_banner_title = getattr(self, 'urgency_banner_title', "Limited Time: Free Solar Assessment + 10% Installation Discount")

            # Homepage sections
            self.testimonial_section_title = getattr(self, 'testimonial_section_title', "What Our Customers Say")
            self.testimonial_section_subtitle = getattr(self, 'testimonial_section_subtitle', "Real stories from real Kenyans who chose solar energy with Olivian Solar and never looked back")
            self.hero_featured_customers_count = getattr(self, 'hero_featured_customers_count', "500+")

            # Colors
            self.primary_color = getattr(self, 'primary_color', '#38b6ff')
            self.secondary_color = getattr(self, 'secondary_color', '#ffffff')

            # Contact Information
            self.sales_email = getattr(self, 'sales_email', '')
            self.sales_phone = getattr(self, 'sales_phone', '')
            self.support_email = getattr(self, 'support_email', '')
            self.support_phone = getattr(self, 'support_phone', '')
            self.whatsapp_number = getattr(self, 'whatsapp_number', '')

            # Social Media
            self.facebook_url = getattr(self, 'facebook_url', '')
            self.twitter_url = getattr(self, 'twitter_url', '')
            self.linkedin_url = getattr(self, 'linkedin_url', '')
            self.instagram_url = getattr(self, 'instagram_url', '')
            self.youtube_url = getattr(self, 'youtube_url', '')

            # Business Hours
            self.business_hours_weekday = getattr(self, 'business_hours_weekday', '8:00 AM - 6:00 PM')
            self.business_hours_saturday = getattr(self, 'business_hours_saturday', '9:00 AM - 4:00 PM')
            self.business_hours_sunday = getattr(self, 'business_hours_sunday', 'Closed')
            self.showroom_hours_weekday = getattr(self, 'showroom_hours_weekday', '')
            self.showroom_hours_saturday = getattr(self, 'showroom_hours_saturday', '')
            self.showroom_hours_sunday = getattr(self, 'showroom_hours_sunday', '')

            # Location & Maps
            self.google_maps_url = getattr(self, 'google_maps_url', '')
            self.google_maps_embed_url = getattr(self, 'google_maps_embed_url', '')

            # Payment Integration - M-Pesa
            self.mpesa_business_name = getattr(self, 'mpesa_business_name', '')
            self.mpesa_paybill_number = getattr(self, 'mpesa_paybill_number', '')
            self.mpesa_account_number = getattr(self, 'mpesa_account_number', '')
            self.mpesa_phone_number = getattr(self, 'mpesa_phone_number', '')
            self.mpesa_till_number = getattr(self, 'mpesa_till_number', '')

            # Business details
            self.registration_number = getattr(self, 'registration_number', '')
            self.tax_number = getattr(self, 'tax_number', '')

            # Bank details
            self.bank_name = getattr(self, 'bank_name', '')
            self.bank_account_number = getattr(self, 'bank_account_number', '')
            self.bank_branch = getattr(self, 'bank_branch', '')

            # Statistics
            self.projects_completed = getattr(self, 'projects_completed', '100+')
            self.total_capacity = getattr(self, 'total_capacity', '1MW+')
            self.customer_satisfaction = getattr(self, 'customer_satisfaction', '98.5%')
            self.founded_year = getattr(self, 'founded_year', 2020)
            self.cities_served = getattr(self, 'cities_served', '20+')
            self.co2_saved_tons = getattr(self, 'co2_saved_tons', '450+')
            self.happy_customers = getattr(self, 'happy_customers', '75')
            self.years_experience = getattr(self, 'years_experience', '3')

            # Trust badges
            self.trust_badge_1_icon = getattr(self, 'trust_badge_1_icon', 'fas fa-certificate')
            self.trust_badge_1_text = getattr(self, 'trust_badge_1_text', 'IEC Certified')
            self.trust_badge_2_icon = getattr(self, 'trust_badge_2_icon', 'fas fa-shield-alt')
            self.trust_badge_2_text = getattr(self, 'trust_badge_2_text', '10-Year Warranty')
            self.trust_badge_3_icon = getattr(self, 'trust_badge_3_icon', 'fas fa-users')
            self.trust_badge_3_text = getattr(self, 'trust_badge_3_text', '500+ Customers')
            self.trust_badge_4_icon = getattr(self, 'trust_badge_4_icon', 'fas fa-award')
            self.trust_badge_4_text = getattr(self, 'trust_badge_4_text', 'Best Service 2024')

            # System settings
            self.default_currency = getattr(self, 'default_currency', 'KES')
            self.vat_rate = getattr(self, 'vat_rate', 16.00)
            self.installation_fee = getattr(self, 'installation_fee', 15000.00)

        def get_whatsapp_url(self):
            phone = getattr(self, 'phone', '+254-719-728-666').replace('+', '').replace('-', '').replace(' ', '')
            return f"https://wa.me/{phone}"

        def get_social_media_links(self):
            return {
                'facebook': getattr(self, 'facebook_url', ''),
                'twitter': getattr(self, 'twitter_url', ''),
                'linkedin': getattr(self, 'linkedin_url', ''),
                'instagram': getattr(self, 'instagram_url', ''),
                'youtube': getattr(self, 'youtube_url', ''),
            }

        def has_social_media(self):
            links = self.get_social_media_links()
            return any(links.values())

    try:
        # Try to load company settings from database
        company_settings = CompanySettings.get_settings()
        company = CompanyWrapper(company_settings)
    except Exception as e:
        # Fallback to settings-based configuration if database is not available
        company = CompanyWrapper()
        company.name = getattr(settings, 'COMPANY_NAME', 'The Olivian Group Limited')
        company.primary_color = getattr(settings, 'PRIMARY_COLOR', '#38b6ff')
        company.secondary_color = getattr(settings, 'SECONDARY_COLOR', '#ffffff')
        company.phone = getattr(settings, 'COMPANY_PHONE', '+254-719-728-666')
        company.email = getattr(settings, 'COMPANY_EMAIL', 'info@olivian.co.ke')
        company.address = getattr(settings, 'COMPANY_ADDRESS', 'Nairobi, Kenya')
        company.website = getattr(settings, 'COMPANY_WEBSITE', 'https://olivian.co.ke')
        company.about_description = getattr(settings, 'COMPANY_ABOUT', 'Professional solar solutions for homes and businesses in Kenya.')
        company.meta_description = getattr(settings, 'COMPANY_META_DESCRIPTION', company.about_description)
        company.meta_keywords = getattr(settings, 'COMPANY_META_KEYWORDS', 'solar panels Kenya, solar installation, solar energy, renewable energy')
        company.tagline = getattr(settings, 'COMPANY_TAGLINE', 'Professional Solar Solutions')
    
    return {
        'company': company,
        'whatsapp_url': company.get_whatsapp_url(),
        'social_media': company.get_social_media_links(),
        'has_social_media': company.has_social_media(),
        'team_members': [],  # Empty list as fallback
        'featured_projects': [],  # Empty list as fallback
        'FACEBOOK_APP_ID': getattr(settings, 'FACEBOOK_APP_ID', ''),
    }

def currency_info(request):
    """Add currency information to template context"""
    return {
        'default_currency': getattr(settings, 'DEFAULT_CURRENCY', 'KES'),
        'vat_rate': getattr(settings, 'VAT_RATE', 16.0),
    }

def google_maps_api_key(request):
    """Context processor to make Google Maps API key available in all templates"""
    return {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
    }
    
def cart_info(request):
    """Add cart information to template context for authenticated users"""
    if request.user.is_authenticated:
        try:
            from apps.ecommerce.models import ShoppingCart
            cart = ShoppingCart.objects.filter(user=request.user).first()
            cart_count = cart.total_items if cart else 0
            return {
                'cart_count': cart_count,
                'has_cart_items': cart_count > 0,
            }
        except Exception as e:
            # Fallback if cart system is not available
            return {
                'cart_count': 0,
                'has_cart_items': False,
            }
    else:
        return {
            'cart_count': 0,
            'has_cart_items': False,
        }

def active_discounts(request):
    """Add active discount information to template context"""
    try:
        # Get all currently active holidays
        all_holidays = KenyanHoliday.objects.filter(is_active=True)

        # Manually filter holidays that are currently active
        active_holidays = []
        for holiday in all_holidays:
            if holiday.is_currently_active:
                active_holidays.append(holiday)

        if active_holidays:
            # Special rule: Jamhuri Day gets priority over Christmas from Dec 1-12
            import datetime
            today = datetime.date.today()
            is_jamhuri_priority_period = (today.month == 12 and today.day <= 12)

            # Sort by holiday date ascending (earlier holidays first for chronological prioritization)
            # But apply Jamhuri priority override for Dec 1-12
            def get_holiday_date(holiday):
                """Get comparable holiday date tuple (month, day) for sorting"""
                if is_jamhuri_priority_period and holiday.name == 'Jamhuri Day':
                    return (12, 1)  # Force Jamhuri to sort first during priority period
                elif holiday.date_type == 'fixed' and holiday.fixed_month and holiday.fixed_day:
                    return (holiday.fixed_month, holiday.fixed_day)
                elif holiday.name == 'Christmas/New Year':
                    return (12, 25)  # Christmas date for sorting
                else:
                    # Default fallback
                    return (holiday.fixed_month or 99, holiday.fixed_day or 99)

            active_holidays.sort(key=get_holiday_date)

            # Select the first holiday offer that has discount_percentage (respect sorted order)
            holiday_offer = None
            for holiday in active_holidays:
                offer = HolidayOffer.objects.filter(
                    holiday=holiday,
                    is_active=True
                ).order_by('priority', 'order').first()
                if offer and offer.discount_percentage:
                    holiday_offer = offer
                    break

            if holiday_offer:
                return {
                    'active_holiday_offer': holiday_offer,
                    'discount_percentage': holiday_offer.discount_percentage,
                    'discount_description': holiday_offer.discount_description or holiday_offer.banner_text,
                    'show_discounted_prices': True,
                    'discount_type': 'holiday_offer',
                }



        return {
            'active_holiday_offer': None,
            'discount_percentage': 0,
            'discount_description': '',
            'show_discounted_prices': False,
            'discount_type': None,
        }

    except Exception as e:
        # Fallback if database is not ready
        return {
            'active_holiday_offer': None,
            'discount_percentage': 0,
            'discount_description': '',
            'show_discounted_prices': False,
            'discount_type': None,
        }