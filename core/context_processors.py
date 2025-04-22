from .models import ContactInfo, SiteSettings, MainMenu, SocialLink, FooterSection, Newsletter, PolicyPage, FAQItem
from .forms import QuoteRequestForm

def common_context(request):
    return {
        'contact_info': ContactInfo.objects.first(),
        'site_settings': SiteSettings.objects.first(),
        'quote_form': QuoteRequestForm(),
        'main_menu': MainMenu.objects.all(),
        'social_links': SocialLink.objects.all(),
        'footer_sections': FooterSection.objects.all(),
        'newsletter': Newsletter.objects.first(),
        'languages': [
            {'code': 'en', 'name': 'English'},
            {'code': 'sw', 'name': 'Swahili'},
            {'code': 'ar', 'name': 'Arabic'},
            {'code': 'fr', 'name': 'French'},
            {'code': 'kik', 'name': 'Kikuyu'},
        ],
        'policy_pages': PolicyPage.objects.all(),
        'faq_items': FAQItem.objects.all(),
    }
