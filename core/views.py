import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import translation
from django.conf import settings
from django.contrib import messages
from .models import (
    HeroBanner, WelcomeSection, WhatWeDoItem, Newsletter, 
    QuoteRequest, ContactInfo, SiteSettings, MainMenu,
    SocialLink, FooterSection, FooterLink, AboutBanner,
    Achievement, AboutSection, TeamSection, TeamMember,
    ContactSection, PolicyPage, FAQItem, Certification, AdminNotification
)
from products.models import Product
from django.http import JsonResponse, Http404
from .forms import QuoteRequestForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import timedelta
import json

def home(request):
    hero_banners = HeroBanner.objects.all()
    welcome_section = WelcomeSection.objects.first()
    what_we_do_items = WhatWeDoItem.objects.all()
    contact_info = ContactInfo.objects.first()
    site_settings = SiteSettings.objects.first()
    main_menu = MainMenu.objects.all()
    social_links = SocialLink.objects.all()
    footer_sections = FooterSection.objects.all()
    
    # Get newsletter settings (first record or create default)
    newsletter_settings = Newsletter.objects.first()
    if not newsletter_settings:
        newsletter_settings = Newsletter.objects.create(
            email="default@example.com",  # This is just a placeholder
            title="Subscribe to Our Newsletter",
            description="Stay updated with our latest news and offers."
        )

    # Products pagination
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 2)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    # Language options
    languages = [
        {'code': 'en', 'name': 'English'},
        {'code': 'sw', 'name': 'Swahili'},
        {'code': 'ar', 'name': 'Arabic'},
        {'code': 'fr', 'name': 'French'},
        {'code': 'kik', 'name': 'Kikuyu'},
    ]

    context = {
        'hero_banners': hero_banners,
        'welcome_section': welcome_section,
        'what_we_do_items': what_we_do_items,
        'products': products,
        'contact_info': contact_info,
        'site_settings': site_settings,
        'main_menu': main_menu,
        'social_links': social_links,
        'footer_sections': footer_sections,
        'languages': languages,
        'newsletter': newsletter_settings,
    }

    return render(request, 'core/home.html', context)

def change_language(request):
    if request.method == 'POST':
        language_code = request.POST.get('language')
        if language_code:
            # Activate the new language
            translation.activate(language_code)
            # Create response object
            response = redirect(request.META.get('HTTP_REFERER', '/'))
            # Set the language cookie
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code)
            # Store language preference in session
            request.session['django_language'] = language_code
            return response
    return redirect('/')

def newsletter_signup(request):
    print("Newsletter signup view called")
    print(f"Request method: {request.method}")
    print(f"POST data: {request.POST}")

    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            name = request.POST.get('name', '')
           
            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email is required'})
           
            # Check if email already exists
            existing_subscriber = Newsletter.objects.filter(email=email).first()
           
            if existing_subscriber:
                if existing_subscriber.is_active:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'You are already subscribed to our newsletter!'
                    })
                else:
                    # Reactivate the subscriber
                    existing_subscriber.is_active = True
                    existing_subscriber.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Your subscription has been reactivated!'
                    })
           
            # Create a new subscriber with confirmation token
            token = uuid.uuid4().hex
            subscriber = Newsletter.objects.create(
                email=email,
                name=name,
                confirmation_token=token,
                confirmed=False
            )
           
            # Send confirmation email
            try:
                confirmation_url = request.build_absolute_uri(
                    reverse('core:confirm_subscription', args=[token])
                )
               
                context = {
                    'confirmation_url': confirmation_url,
                    'name': name if name else 'there',
                    'site_name': SiteSettings.objects.first().site_name if SiteSettings.objects.exists() else 'Our Website'
                }
               
                html_message = render_to_string('core/emails/confirm_subscription.html', context)
                plain_message = strip_tags(html_message)
               
                send_mail(
                    f"Confirm your newsletter subscription",
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
               
                return JsonResponse({
                    'status': 'success',
                    'message': 'Please check your email to confirm your subscription!'
                })
            except Exception as e:
                # If email sending fails, still create the subscription but log the error
                print(f"Error sending confirmation email: {e}")
                return JsonResponse({
                    'status': 'success',
                    'message': 'You have been subscribed to our newsletter!'
                })
        except Exception as e:
            print(f"Newsletter signup error: {e}")
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})
   
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def confirm_subscription(request, token):
    subscriber = Newsletter.objects.filter(confirmation_token=token, is_active=True).first()
    
    if subscriber:
        subscriber.confirmed = True
        subscriber.confirmation_token = None  # Clear the token for security
        subscriber.save()
        messages.success(request, 'Your subscription has been confirmed. Thank you!')
    else:
        messages.error(request, 'Invalid or expired confirmation link.')
    
    return redirect('core:home')

def quote_request(request):
    """Handle quote request submissions"""
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            quote_request = form.save()

            # Create admin notification
            AdminNotification.objects.create(
                type='quote',
                title=f"New Quote Request from {quote_request.name}",
                message=f"A new quote request has been submitted by {quote_request.name} ({quote_request.email}).",
                related_object_id=quote_request.id
            )

            # Send email notification to admin
            try:
                subject = f"New Quote Request from {quote_request.name}"
                html_message = render_to_string('core/emails/quote_request_notification.html', {
                    'quote': quote_request,
                    'site_name': SiteSettings.objects.first().site_name,
                })

                send_mail(
                    subject=subject,
                    message=f"New quote request received from {quote_request.name}. Please check admin panel.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    html_message=html_message,
                    fail_silently=True,
                )

                # Send confirmation email to customer
                customer_subject = "Thank you for your quote request"
                customer_html_message = render_to_string('core/emails/quote_request_confirmation.html', {
                    'name': quote_request.name,
                    'site_name': SiteSettings.objects.first().site_name,
                    'contact_info': ContactInfo.objects.first(),
                })

                send_mail(
                    subject=customer_subject,
                    message=f"Thank you for your quote request. We'll get back to you soon.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[quote_request.email],
                    html_message=customer_html_message,
                    fail_silently=True,
                )

            except Exception as e:
                # Log the error but don't prevent the form submission
                print(f"Email sending error: {e}")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Your quote request has been submitted successfully. We will contact you shortly.'
                })
            else:
                messages.success(request, 'Your quote request has been submitted successfully. We will contact you shortly.')
                return redirect('core:home')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors.as_json()
                })

    else:
        form = QuoteRequestForm()

    # This is for GET requests or if form is invalid
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        })

    return redirect('core:home')

def about(request):
    context = {
        'banner': AboutBanner.objects.first(),
        'achievements': Achievement.objects.all(),
        'about_section': AboutSection.objects.first(),
        'team_section': TeamSection.objects.first(),
        'team_members': TeamMember.objects.all(),
        'contact_section': ContactSection.objects.first(),
    }
    return render(request, 'core/about.html', context)

def policy_page(request, policy_type):
    """View for displaying policy pages like privacy policy, terms, etc."""
    try:
        policy = PolicyPage.objects.get(type=policy_type, is_published=True)
        
        # Check if the content is still the default content
        default_content_map = {
            'privacy': '<h2>Privacy Policy</h2><p>This is a default privacy policy. Please update this content in the admin panel.</p>',
            'terms': '<h2>Terms & Conditions</h2><p>This is a default terms and conditions page. Please update this content in the admin panel.</p>',
            'refund': '<h2>Return & Refund Policy</h2><p>This is a default return and refund policy. Please update this content in the admin panel.</p>',
            'shipping': '<h2>Shipping & Delivery</h2><p>This is a default shipping and delivery information page. Please update this content in the admin panel.</p>',
            'environment': '<h2>Our Environmental Commitment</h2><p>This is a default environmental commitment page. Please update this content in the admin panel.</p>',
            'certifications': '<h2>Our Certifications & Standards</h2><p>This is a default certifications page. Please update this content in the admin panel.</p>',
        }
        
        # If the policy content exactly matches the default content, treat it as not populated
        if policy_type in default_content_map and policy.content.strip() == default_content_map[policy_type].strip():
            # Show a message to the admin users that this is default content
            if request.user.is_staff:
                from django.contrib import messages
                messages.warning(request, f"This {policy.title} page is showing default content. Please update it in the admin panel.")
        
        return render(request, 'core/policy_page.html', {
            'policy': policy,
            'contact_info': ContactInfo.objects.first(),
            'site_settings': SiteSettings.objects.first(),
            'main_menu': MainMenu.objects.all(),
            'social_links': SocialLink.objects.all(),
            'footer_sections': FooterSection.objects.all(),
        })
        
    except PolicyPage.DoesNotExist:
        # If the policy doesn't exist yet, show a template with default content
        # Only show this to admin users, regular users get a "coming soon" message
        if request.user.is_staff:
            return render(request, 'core/policy_page_default.html', {
                'policy_type': policy_type,
                'title': dict(PolicyPage.POLICY_TYPES).get(policy_type, 'Policy Page'),
                'contact_info': ContactInfo.objects.first(),
                'site_settings': SiteSettings.objects.first(),
                'main_menu': MainMenu.objects.all(),
                'social_links': SocialLink.objects.all(),
                'footer_sections': FooterSection.objects.all(),
            })
        else:
            # For regular users, show a "coming soon" message
            return render(request, 'core/policy_coming_soon.html', {
                'title': dict(PolicyPage.POLICY_TYPES).get(policy_type, 'Policy Page'),
                'contact_info': ContactInfo.objects.first(),
                'site_settings': SiteSettings.objects.first(),
                'main_menu': MainMenu.objects.all(),
                'social_links': SocialLink.objects.all(),
                'footer_sections': FooterSection.objects.all(),
            })


def faqs(request):
    """View for displaying FAQs page with categorized questions."""
    # Get all FAQ items
    all_faqs = FAQItem.objects.all()
    
    # Group FAQs by category
    categories = {}
    for faq in all_faqs:
        category = faq.category or 'General'
        if category not in categories:
            categories[category] = []
        categories[category].append(faq)
    
    # Get policy page content if it exists
    try:
        faq_policy = PolicyPage.objects.get(type='faq', is_published=True)
        
        # Check if the content is still the default content
        default_content = '<h2>Frequently Asked Questions</h2><p>Below you\'ll find answers to the most common questions about our products and services.</p>'
        
        # If the policy content exactly matches the default content and we have actual FAQs, don't show it
        if faq_policy.content.strip() == default_content.strip() and all_faqs.exists():
            faq_policy = None
            
            # Show a message to admin users
            if request.user.is_staff:
                from django.contrib import messages
                messages.warning(request, "The FAQ introduction is showing default content. Please update it in the admin panel.")
    
    except PolicyPage.DoesNotExist:
        faq_policy = None

    return render(request, 'core/faqs.html', {
        'categories': categories,
        'faq_policy': faq_policy,
        'contact_info': ContactInfo.objects.first(),
        'site_settings': SiteSettings.objects.first(),
        'main_menu': MainMenu.objects.all(),
        'social_links': SocialLink.objects.all(),
        'footer_sections': FooterSection.objects.all(),
    })

def certifications(request):
    """View for displaying certifications and standards."""
    certifications_list = Certification.objects.all().order_by('order', 'name')

    # Get policy page content if it exists
    try:
        cert_policy = PolicyPage.objects.get(type='certifications', is_published=True)
        
        # Check if the content is still the default content
        default_content = '<h2>Our Certifications & Standards</h2><p>This is a default certifications page. Please update this content in the admin panel.</p>'
        is_default = cert_policy.content.strip() == default_content.strip()

        # If it's still the default content and we have actual certifications, don't show the policy
        if is_default and certifications_list.exists():
            cert_policy = None
    except PolicyPage.DoesNotExist:
        cert_policy = None
    
    return render(request, 'core/certifications.html', {
        'certifications': certifications_list,
        'cert_policy': cert_policy,
        'contact_info': ContactInfo.objects.first(),
        'site_settings': SiteSettings.objects.first(),
        'main_menu': MainMenu.objects.all(),
        'social_links': SocialLink.objects.all(),
        'footer_sections': FooterSection.objects.all(),
    })

@staff_member_required
def quote_analytics(request):
    """View for displaying quote request analytics"""
    # Get date range from request or use default (last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get quote requests in date range
    quotes = QuoteRequest.objects.filter(created_at__gte=start_date)
    
    # Daily quote requests
    daily_quotes = quotes.annotate(day=TruncDay('created_at')) \
                         .values('day') \
                         .annotate(count=Count('id')) \
                         .order_by('day')
    
    # Status distribution
    status_counts = quotes.values('status') \
                          .annotate(count=Count('id')) \
                          .order_by('status')
    
    # Convert to JSON for charts
    daily_data = json.dumps([{
        'date': item['day'].strftime('%Y-%m-%d'),
        'count': item['count']
    } for item in daily_quotes])
    
    status_data = json.dumps([{
        'status': item['status'],
        'count': item['count']
    } for item in status_counts])
    
    return render(request, 'admin/quote_analytics.html', {
        'daily_data': daily_data,
        'status_data': status_data,
        'total_quotes': quotes.count(),
        'days': days,
    })