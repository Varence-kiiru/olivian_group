from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponse, FileResponse, StreamingHttpResponse
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Sum, Count, Avg, Max, F, ExpressionWrapper, DurationField, Prefetch
from django.db.models.functions import Now
from django.views import View
from django.utils import timezone
from .models import Notification, CompanySettings, ActivityLog, ProjectShowcase, LegalDocument, CookieConsent, CookieCategory, Testimonial, VideoTutorial, ServiceArea, NewsletterCampaign, NewsletterSubscriber
from apps.financial.models import Transaction
from django.core import serializers
from django.core.management import call_command
from django.conf import settings
from django.contrib import messages
from django.utils.text import slugify
from datetime import datetime
import os
import csv
import json
import subprocess
import zipfile
import tempfile
import logging
import hashlib
import platform
import django
import psutil
from django.db import connection
import sys
import shutil

User = get_user_model()

# Initialize logger
logger = logging.getLogger(__name__)

class HomeView(TemplateView):
    template_name = 'website/home.html'

    def parse_capacity_value(self, capacity_str):
        """Parse capacity string like '1.5MW+', '200kW' into float"""
        if not capacity_str:
            return 0

        try:
            # Remove units and special characters, keep only digits and decimal points
            clean_str = ''.join(c for c in capacity_str if c.isdigit() or c == '.')
            if clean_str:
                return float(clean_str)
        except (ValueError, TypeError):
            pass

        return 0

    def parse_projects_value(self, projects_str):
        """Parse projects string like '100+', '250' into int"""
        if not projects_str:
            return 0

        try:
            # Remove non-numeric characters and convert to int
            clean_str = ''.join(c for c in projects_str if c.isdigit())
            if clean_str:
                return int(clean_str)
        except (ValueError, TypeError):
            pass

        return 0

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get statistics from projects and project showcases
        try:
            # Import here to avoid circular imports
            from apps.projects.models import Project

            # Calculate real statistics from projects
            completed_projects = Project.objects.filter(status='completed')
            total_projects = completed_projects.count()

            # Calculate total capacity from completed projects
            total_capacity = completed_projects.aggregate(
                total=Sum('system_capacity')
            )['total'] or 0

            # Get unique cities from projects for cities served
            cities_served = Project.objects.exclude(
                city__isnull=True
            ).exclude(city__exact='').values('city').distinct().count()

            # Estimate CO2 saved (1kW saves approximately 1.2 tons CO2 per year)
            co2_saved = round(float(total_capacity) * 1.2, 1) if total_capacity else 0

            # Recent completed projects for showcase (limit to 3)
            recent_projects = completed_projects.order_by('-created_at')[:3]

        except Exception as e:
            # Fallback to ProjectShowcase if Project model is not available
            project_showcases = ProjectShowcase.objects.all()
            total_projects = project_showcases.count()

            # Calculate capacity from showcases (parse capacity strings like "15kW", "200kW")
            total_capacity = 0
            for showcase in project_showcases:
                try:
                    # Extract numeric value from capacity string
                    capacity_str = showcase.capacity.replace('kW', '').replace('MW', '000').strip()
                    if capacity_str.replace('.', '').isdigit():
                        total_capacity += float(capacity_str)
                except (AttributeError, ValueError):
                    pass

            # Get unique locations for cities served
            cities_served = project_showcases.exclude(
                location__isnull=True
            ).exclude(location__exact='').values('location').distinct().count()

            # Estimate CO2 saved
            co2_saved = round(total_capacity * 1.2, 1) if total_capacity else 0

            # Use project showcases as recent projects
            recent_projects = project_showcases.filter(is_featured=True).order_by('order')[:3]

        # Format capacity display
        if total_capacity >= 1000:
            capacity_display = f"{total_capacity/1000:.1f}MW"
        else:
            capacity_display = f"{total_capacity:.0f}kW"

        # Calculate reasonable statistics based on projects and capacity
        company = CompanySettings.objects.first()
        company_projects = self.parse_projects_value(company.projects_completed) if company and company.projects_completed else total_projects
        company_capacity = self.parse_capacity_value(company.total_capacity) if company and company.total_capacity else total_capacity

        # Calculate cities served reasonably based on projects and capacity
        # Average project size determines reach - larger projects cover more cities
        avg_project_size = company_capacity / max(1, company_projects)  # kW per project
        if avg_project_size > 100:  # Large commercial projects
            cities_served_calculated = min(company_projects * 2, cities_served or company_projects)
        elif avg_project_size > 20:  # Medium residential/commercial
            cities_served_calculated = min(company_projects, cities_served or company_projects)
        else:  # Small residential projects
            cities_served_calculated = min(max(1, company_projects // 3), cities_served or company_projects)

        # Ensure minimum of 1 if there are projects
        print(f"DEBUG: cities_served_calculated before max: {cities_served_calculated}, type: {type(cities_served_calculated)}")
        print(f"DEBUG: cities_served: {cities_served}, type: {type(cities_served)}")
        cities_served_calculated = max(1, cities_served_calculated) if company_projects > 0 else cities_served
        print(f"DEBUG: cities_served_calculated after max: {cities_served_calculated}, type: {type(cities_served_calculated)}")

        # Calculate CO2 saved reasonably based on capacity and realistic usage
        # More conservative estimate: 0.8-1.0 tons CO2 per kW per year
        # Monthly savings is more traditional, annual can vary
        base_co2_factor = 0.9  # Base factor for average usage
        # Adjust based on capacity scale - larger installations may have different efficiency
        if company_capacity > 500:
            co2_factor = base_co2_factor * 1.1  # Large systems more efficient
        elif company_capacity > 100:
            co2_factor = base_co2_factor  # Medium systems typical
        else:
            co2_factor = base_co2_factor * 0.9  # Small systems might be less utilized

        co2_saved_calculated = int(company_capacity * co2_factor) if company_capacity > 0 else int(co2_saved)

        if company:
            context['stats'] = {
                'projects_completed': company.projects_completed or total_projects,
                'total_capacity': self.parse_capacity_value(company.total_capacity) if company.total_capacity else total_capacity,
                'total_capacity_display': company.total_capacity or capacity_display,
                'cities_served': company.cities_served or cities_served,  # Now controlled directly in admin
                'co2_saved_tons': company.co2_saved_tons or int(co2_saved),  # Now controlled directly in admin
            }
        else:
            # Fallback to dynamic calculations if no company settings
            context['stats'] = {
                'projects_completed': total_projects,
                'total_capacity': total_capacity,
                'total_capacity_display': capacity_display,
                'cities_served': cities_served_calculated,
                'co2_saved_tons': co2_saved_calculated,
            }

        # Add recent projects to context
        context['recent_projects'] = recent_projects

        # Get featured products for homepage showcase
        try:
            from apps.products.models import Product
            featured_products = Product.objects.filter(
                status='active',
                show_to_customers=True,
                featured=True
            ).select_related('category').prefetch_related('images')[:6]  # Limit to 6 featured products

            context['featured_products'] = featured_products
        except Exception as e:
            # Fallback if products app is not available
            context['featured_products'] = []

        # Get featured blog posts for homepage showcase
        try:
            from apps.blog.models import Post
            featured_blog_posts = Post.objects.filter(
                is_featured=True,
                status='published'
            ).select_related('author', 'category').prefetch_related('tags')[:3]  # Limit to 3 featured posts

            context['featured_blog_posts'] = featured_blog_posts
        except Exception as e:
            # Fallback if blog app is not available
            context['featured_blog_posts'] = []

        # Get customer testimonials for homepage showcase
        try:
            # Try to get testimonials from database first
            testimonials = Testimonial.objects.filter(
                is_featured=True
            ).order_by('order')  # Get all featured testimonials

            if testimonials.exists():
                context['testimonials'] = testimonials
            else:
                # Try ProductReview if no database testimonials
                try:
                    from apps.products.models import ProductReview
                    testimonial_reviews = ProductReview.objects.filter(
                        is_approved=True
                    ).select_related('user', 'product').prefetch_related('user__userprofile')[:2]  # Limit to 2 testimonials

                    context['testimonials'] = testimonial_reviews
                except Exception as e:
                    # No testimonials available
                    context['testimonials'] = []
        except Exception as e:
            # Fallback if testimonials model is not available
            context['testimonials'] = []

        # Add today for date comparisons
        context['today'] = timezone.now().date()

        # Get active holiday offer for banner display
        context['active_holiday_offer'] = self.get_active_holiday_offer()

        return context

    def get_active_holiday_offer(self):
        """Get the current active holiday offer for banner display using chronological prioritization"""
        try:
            # Import here to avoid circular imports
            from .models import HolidayOffer, KenyanHoliday

            # Get all currently active holidays
            all_holidays = KenyanHoliday.objects.filter(is_active=True)
            active_holidays = []
            for holiday in all_holidays:
                if holiday.is_currently_active:
                    active_holidays.append(holiday)

            if active_holidays:
                # Special rule: Jamhuri Day gets priority over Christmas from Dec 1-12
                today = timezone.now().date()
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

                # Get the first (highest priority) holiday offer
                holiday_offer = HolidayOffer.objects.filter(
                    holiday__in=active_holidays,
                    is_active=True
                ).order_by('priority', 'order').first()

                if holiday_offer:
                    return holiday_offer

            return None

        except Exception as e:
            # If holiday system is not available, return None
            return None

class AboutView(TemplateView):
    template_name = 'website/about.html'

class ServicesView(TemplateView):
    template_name = 'website/services.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add Google Maps API key for the coverage check modal
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
        return context

class HelpView(TemplateView):
    """Customer-focused help and support page for public website"""
    template_name = 'website/help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get company settings for contact info
        try:
            company = CompanySettings.get_settings()
        except:
            company = None

        # Get video tutorials
        video_tutorials = VideoTutorial.objects.filter(is_active=True).order_by('-is_featured', 'order', 'title')

        context.update({
            'page_title': 'Help & Support',
            'meta_description': 'Get help and support for Olivian solar products, services, and account management.',
            'company': company,
            'help_categories': self.get_help_categories(),
            'video_tutorials': video_tutorials
        })

        return context

    def get_help_categories(self):
        """Return customer-focused help categories for public website"""
        return [
            {
                'title': 'Getting Started',
                'icon': 'fas fa-rocket',
                'description': 'Learn how to get started with our solar products and services',
                'sections': [
                    {
                        'title': 'Account & Registration',
                        'items': [
                            {'question': 'How do I create an account?', 'answer': 'Click "Sign In" and select "Get Started" to register. You can sign up with email or phone for easy access to quotes and order tracking.'},
                            {'question': 'Do I need an account to request a quote?', 'answer': 'No, you can request quotes through our contact form or solar calculator without an account. However, creating an account allows you to track your quotes and orders.'},
                            {'question': 'How do I reset my password?', 'answer': 'Click "Forgot Password" on the login page. Enter your email or phone number and we\'ll send you a reset link.'},
                        ]
                    },
                    {
                        'title': 'Understanding Solar Solutions',
                        'items': [
                            {'question': 'What solar products do you offer?', 'answer': 'We offer complete solar systems including panels, inverters, batteries, and installation services for homes and businesses.'},
                            {'question': 'How does solar energy work?', 'answer': 'Solar panels convert sunlight into electricity through photovoltaic cells. This clean energy can power your home and reduce electricity bills.'},
                            {'question': 'Is solar right for my property?', 'answer': 'Most properties are suitable. We provide free site assessments to determine the best solar solution for your specific location and energy needs.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Requesting Quotes',
                'icon': 'fas fa-calculator',
                'description': 'Get personalized solar quotes and pricing information',
                'sections': [
                    {
                        'title': 'Solar Calculator',
                        'items': [
                            {'question': 'How do I use the solar calculator?', 'answer': 'Enter your location, monthly electricity bill, and roof details. The calculator will estimate system size and savings.'},
                            {'question': 'Is the solar calculator accurate?', 'answer': 'The calculator provides estimates based on your inputs. We provide detailed quotes after a site assessment for precision.'},
                            {'question': 'What information do you need for a quote?', 'answer': 'Location, current electricity usage, roof orientation, available space, and preferred system type.'},
                        ]
                    },
                    {
                        'title': 'Getting Professional Quotes',
                        'items': [
                            {'question': 'How do I request a detailed quote?', 'answer': 'Use our contact form, call us directly, or fill out the online quotation request form. We respond within 24 hours.'},
                            {'question': 'Is the site assessment free?', 'answer': 'Yes, we provide free site assessments and basic consultations. Detailed system design may have minimal fees for large installations.'},
                            {'question': 'How long does the quoting process take?', 'answer': 'Basic quotes: 24-48 hours. Detailed proposals with site assessment: 3-5 business days.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Orders & Delivery',
                'icon': 'fas fa-truck',
                'description': 'Track your orders and understand our delivery process',
                'sections': [
                    {
                        'title': 'Placing Orders',
                        'items': [
                            {'question': 'How do I place an order?', 'answer': 'After quote approval, we create a project order. You can track progress through your account dashboard.'},
                            {'question': 'What payment methods do you accept?', 'answer': 'M-Pesa, bank transfers, and credit cards. M-Pesa is preferred for faster processing. 50% deposit required for projects.'},
                            {'question': 'Can I modify my order after placement?', 'answer': 'Yes, contact us within 24 hours of order confirmation. Changes may affect delivery timelines.'},
                        ]
                    },
                    {
                        'title': 'Delivery & Installation',
                        'items': [
                            {'question': 'What are your delivery areas?', 'answer': 'We deliver throughout Nairobi and surrounding areas. Remote locations may require special arrangements.'},
                            {'question': 'How long does delivery take?', 'answer': 'Standard delivery: 3-7 business days. Installation: 1-2 weeks after delivery. Express options available.'},
                            {'question': 'Do you provide installation services?', 'answer': 'Yes, we provide professional installation with certified technicians. Installation is included in most packages.'},
                        ]
                    },
                    {
                        'title': 'Order Tracking',
                        'items': [
                            {'question': 'How do I track my order?', 'answer': 'Use the tracking link sent via SMS/email, or log into your account to view order status and project progress.'},
                            {'question': 'Will I receive updates on my order?', 'answer': 'Yes, you\'ll receive SMS and email updates at key milestones: order confirmation, delivery, and installation completion.'},
                            {'question': 'What if my order is delayed?', 'answer': 'We\'ll notify you immediately and provide updated timelines. Contact us for status updates.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Products & Warranties',
                'icon': 'fas fa-shield-alt',
                'description': 'Learn about our products and warranty coverage',
                'sections': [
                    {
                        'title': 'Product Information',
                        'items': [
                            {'question': 'What warranties do you offer?', 'answer': 'Solar panels: 25 years, Inverters: 5-10 years, Batteries: 5 years, Installation workmanship: 2 years.'},
                            {'question': 'Do you offer maintenance services?', 'answer': 'Yes, we provide annual maintenance packages and emergency repair services for warranty and out-of-warranty systems.'},
                            {'question': 'What if a product is defective?', 'answer': 'Contact us immediately. We\'ll arrange replacement or repair under warranty. Most issues are resolved within 48 hours.'},
                        ]
                    },
                    {
                        'title': 'Technical Specifications',
                        'items': [
                            {'question': 'What solar panel efficiency can I expect?', 'answer': 'Our panels range from 18-22% efficiency. Higher efficiency panels produce more power in limited space.'},
                            {'question': 'How do I know what battery capacity I need?', 'answer': 'This depends on your backup requirements. We recommend 1-3 days of autonomy for most residential systems.'},
                            {'question': 'Can I expand my system later?', 'answer': 'Yes, most systems are designed for future expansion. Contact us to discuss upgrade options.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Support & Contact',
                'icon': 'fas fa-headset',
                'description': 'Get help and contact our support team',
                'sections': [
                    {
                        'title': 'Customer Support',
                        'items': [
                            {'question': 'How do I contact customer support?', 'answer': 'Call us at our support line, use the contact form, or email support@olivian.co.ke. We respond within 4 hours.'},
                            {'question': 'What are your support hours?', 'answer': 'Monday-Friday 8:00 AM - 6:00 PM EAT. Emergency support available 24/7 for active projects.'},
                            {'question': 'Do you offer emergency repairs?', 'answer': 'Yes, emergency repairs are available 24/7 for systems under warranty or maintenance contracts.'},
                        ]
                    },
                    {
                        'title': 'Billing & Payments',
                        'items': [
                            {'question': 'How do I pay for my order?', 'answer': 'M-Pesa is preferred for instant processing. Bank transfers and cards also accepted. 50% deposit required for projects.'},
                            {'question': 'What is your refund policy?', 'answer': '30-day return policy for unused products. Refunds processed within 7-14 business days. Installation fees are non-refundable.'},
                            {'question': 'Do you offer financing options?', 'answer': 'Yes, we partner with financing companies for solar loans. Contact us to discuss payment plans.'},
                        ]
                    },
                    {
                        'title': 'Technical Issues',
                        'items': [
                            {'question': 'My solar system isn\'t working properly', 'answer': 'Check circuit breakers and connections first. Contact our technical support team immediately for diagnosis.'},
                            {'question': 'How do I monitor my system performance?', 'answer': 'We provide monitoring apps and dashboards. Contact us for setup assistance.'},
                            {'question': 'What should I do in case of power outages?', 'answer': 'Solar systems with batteries provide backup power automatically. Contact us if backup fails.'},
                        ]
                    }
                ]
            }
        ]

class StaffHelpView(LoginRequiredMixin, TemplateView):
    """Staff help and support page for internal team members"""
    template_name = 'dashboard/staff_help.html'

    def dispatch(self, request, *args, **kwargs):
        # Only allow staff roles to access staff help
        staff_roles = ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person', 'project_manager', 'inventory_manager', 'cashier', 'technician']
        if request.user.role not in staff_roles:
            from django.contrib import messages
            messages.error(request, 'Access denied. Staff help is only available to team members.')
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get company settings for contact info
        try:
            company = CompanySettings.get_settings()
        except:
            company = None

        context.update({
            'page_title': 'Staff Help & Support',
            'page_subtitle': 'Internal procedures and system documentation',
            'help_categories': self.get_staff_help_categories(),
            'user_role': self.request.user.get_role_display(),
            'company': company,
        })

        return context

    def get_staff_help_categories(self):
        """Return staff-specific help categories for internal team members"""
        return [
            {
                'title': 'System Access & Security',
                'icon': 'fas fa-shield-alt',
                'description': 'Login procedures, password management, and security protocols',
                'sections': [
                    {
                        'title': 'Account Access',
                        'items': [
                            {'question': 'How do I log into the management system?', 'answer': 'Visit the main website and click "Sign In". Use your email/phone and password. Staff accounts are created by administrators.'},
                            {'question': 'I forgot my password - what should I do?', 'answer': 'Click "Forgot Password" on the login page, or contact your supervisor/IT admin. Temporary passwords are set by admins.'},
                            {'question': 'How do I change my password?', 'answer': 'Go to Profile → Security Settings. Choose a strong password with 8+ characters, mixing letters, numbers, and symbols.'},
                        ]
                    },
                    {
                        'title': 'Security Best Practices',
                        'items': [
                            {'question': 'What are the password requirements?', 'answer': 'Minimum 8 characters, must include uppercase, lowercase, numbers, and special characters. Passwords expire every 90 days.'},
                            {'question': 'Should I share my login credentials?', 'answer': 'Never share your credentials. Each staff member has individual access based on their role. Report suspicious activity immediately.'},
                            {'question': 'How do I report security concerns?', 'answer': 'Contact your supervisor or IT admin immediately. Use the internal reporting system for security incidents.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Sales & Quotations',
                'icon': 'fas fa-file-invoice-dollar',
                'description': 'Creating quotes, managing customers, and sales processes',
                'sections': [
                    {
                        'title': 'Creating Quotations',
                        'items': [
                            {'question': 'How do I create a new quotation?', 'answer': 'Go to Quotations → Create New. Fill in customer details, select products, and the system auto-generates QUO-YYYY-XXXX.'},
                            {'question': 'What information do I need for a quote?', 'answer': 'Customer details, site location, energy requirements, preferred system type, and installation timeline.'},
                            {'question': 'How do I add products to a quotation?', 'answer': 'Use the product selector. Search by category or name, adjust quantities, and see real-time pricing calculations.'},
                        ]
                    },
                    {
                        'title': 'Quotation Workflow',
                        'items': [
                            {'question': 'What happens after I create a quote?', 'answer': 'Quote goes to manager approval, then converts to project (PRJ-YYYY-XXXX) if approved. Customer receives email notification.'},
                            {'question': 'How do I convert a quote to a project?', 'answer': 'Once approved, click "Convert to Project". System creates project record and assigns technicians.'},
                            {'question': 'Can I edit a quotation after creation?', 'answer': 'Yes, until it\'s approved. After approval, create a revision or new quote. All changes are logged for audit.'},
                        ]
                    },
                    {
                        'title': 'Customer Management',
                        'items': [
                            {'question': 'How do I add a new customer?', 'answer': 'Go to CRM → Customers → Add New. Include contact details, location, and customer type (individual/business/government).'},
                            {'question': 'How do I track customer interactions?', 'answer': 'Use the CRM Activities section. Log calls, emails, meetings, and follow-ups. System tracks all customer touchpoints.'},
                            {'question': 'What\'s the lead conversion process?', 'answer': 'Lead → Qualification → Quote → Project. Use CRM pipeline to track progress and set reminders for follow-ups.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Project Management',
                'icon': 'fas fa-project-diagram',
                'description': 'Managing solar installations from planning to completion',
                'sections': [
                    {
                        'title': 'Project Creation & Setup',
                        'items': [
                            {'question': 'How do I create a new project?', 'answer': 'From approved quotation → Convert to Project, or Projects → Create New. System assigns PRJ-YYYY-XXXX automatically.'},
                            {'question': 'What team members do I assign?', 'answer': 'Project Manager (you), Lead Technician, Assistant Technicians, and Customer Liaison based on project complexity.'},
                            {'question': 'How do I set project milestones?', 'answer': 'Use project timeline: Site Assessment → Design Approval → Material Procurement → Installation → Testing → Handover.'},
                        ]
                    },
                    {
                        'title': 'Project Tracking & Updates',
                        'items': [
                            {'question': 'How do I update project progress?', 'answer': 'Use status dropdown: Planning → In Progress → Completed. Add detailed notes, photos, and issue logs.'},
                            {'question': 'What if a project encounters delays?', 'answer': 'Document issues in project notes, notify customer, update timeline, and inform management. Log reasons for delays.'},
                            {'question': 'How do I close out a project?', 'answer': 'Mark as completed, upload final documentation, get customer sign-off, and process final payment.'},
                        ]
                    },
                    {
                        'title': 'Budget & Cost Management',
                        'items': [
                            {'question': 'How do I track project costs?', 'answer': 'Monitor against budget in Projects → Budget tab. Log all expenses and compare to approved budget.'},
                            {'question': 'What if costs exceed budget?', 'answer': 'Stop work and notify management immediately. Create budget revision request with justification.'},
                            {'question': 'How do I process change orders?', 'answer': 'Document change request, get customer approval, update budget, and log in project notes.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Inventory & POS',
                'icon': 'fas fa-boxes',
                'description': 'Managing stock, processing sales, and point-of-sale operations',
                'sections': [
                    {
                        'title': 'Inventory Management',
                        'items': [
                            {'question': 'How do I check current stock levels?', 'answer': 'Go to Inventory → Products. View real-time stock, reorder points, and low-stock alerts.'},
                            {'question': 'How do I add new products to inventory?', 'answer': 'Inventory → Products → Add New. Include SKU, description, pricing, stock levels, and product images.'},
                            {'question': 'What triggers reorder alerts?', 'answer': 'When stock falls below reorder point. System sends notifications to inventory managers and relevant staff.'},
                        ]
                    },
                    {
                        'title': 'Stock Movement',
                        'items': [
                            {'question': 'How do I record stock receipts?', 'answer': 'Inventory → Stock Movements → Add Receipt. Link to purchase order and update warehouse locations.'},
                            {'question': 'How do I transfer stock between warehouses?', 'answer': 'Create transfer request, get approval, process movement, and update both warehouse records.'},
                            {'question': 'How do I handle stock adjustments?', 'answer': 'For damages/losses: Create adjustment record with reason. Requires manager approval for significant adjustments.'},
                        ]
                    },
                    {
                        'title': 'Point of Sale (POS)',
                        'items': [
                            {'question': 'How do I process a sale?', 'answer': 'POS Terminal: Add products → Apply discounts → Collect payment (Cash/M-Pesa/Card) → Print receipt.'},
                            {'question': 'What payment methods are supported?', 'answer': 'Cash, M-Pesa (integrated), Credit/Debit cards. All transactions logged with receipt numbers.'},
                            {'question': 'How do I handle returns/refunds?', 'answer': 'Verify receipt, check return policy (30 days), process refund, update inventory, and log transaction.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Financial Operations',
                'icon': 'fas fa-money-bill-wave',
                'description': 'Managing payments, budgets, and financial records',
                'sections': [
                    {
                        'title': 'Payment Processing',
                        'items': [
                            {'question': 'How do I process customer payments?', 'answer': 'Use POS for immediate payments or Financial → Transactions for bank transfers. M-Pesa integration for mobile money.'},
                            {'question': 'What are the payment terms?', 'answer': '50% deposit required for projects, balance due before installation. Net 30 for approved business customers.'},
                            {'question': 'How do I handle payment disputes?', 'answer': 'Document dispute, contact customer, review records, and escalate to management if needed.'},
                        ]
                    },
                    {
                        'title': 'Expense Management',
                        'items': [
                            {'question': 'How do I submit expenses for approval?', 'answer': 'Create expense request with receipts, select budget category, and submit for manager approval.'},
                            {'question': 'What expenses require pre-approval?', 'answer': 'Anything over KES 10,000 or outside normal operations. Travel, equipment purchases, and large supplies.'},
                            {'question': 'How do I track expense approvals?', 'answer': 'Check status in Expense Requests. Approved expenses auto-post to budgets. Denied requests show reason.'},
                        ]
                    },
                    {
                        'title': 'Budget Monitoring',
                        'items': [
                            {'question': 'How do I check budget utilization?', 'answer': 'Budgets → [Select Budget] → View spending against allocated amounts. System shows alerts for overages.'},
                            {'question': 'What if a department exceeds budget?', 'answer': 'Immediate notification to managers. Work stops until budget revision approved or additional funds allocated.'},
                            {'question': 'How do I create budget revisions?', 'answer': 'Submit revision request with justification. Requires director approval for significant changes.'},
                        ]
                    }
                ]
            },
            {
                'title': 'Technical Support',
                'icon': 'fas fa-tools',
                'description': 'System troubleshooting, maintenance procedures, and technical issues',
                'sections': [
                    {
                        'title': 'System Issues',
                        'items': [
                            {'question': 'What if the system is running slowly?', 'answer': 'Clear browser cache, try different browser, or restart. Contact IT if persistent. System status shown in footer.'},
                            {'question': 'I can\'t log in to the system', 'answer': 'Check credentials, try password reset, or contact IT admin. Account lockout occurs after 5 failed attempts.'},
                            {'question': 'Pages aren\'t loading properly', 'answer': 'Check internet connection, clear cache/cookies, try incognito mode. Report to IT if widespread.'},
                        ]
                    },
                    {
                        'title': 'Data Management',
                        'items': [
                            {'question': 'How do I export customer data?', 'answer': 'Contact admin for data exports. Available in CSV/JSON format. All exports logged for security.'},
                            {'question': 'How secure is our customer data?', 'answer': 'Encrypted at rest and in transit. Regular backups, role-based access control, GDPR compliant.'},
                            {'question': 'How do I backup important data?', 'answer': 'System auto-backups daily. Manual backups available to admins. Never store sensitive data on local machines.'},
                        ]
                    },
                    {
                        'title': 'Equipment & Maintenance',
                        'items': [
                            {'question': 'How do I report equipment issues?', 'answer': 'Log in maintenance system or contact facilities manager. Include photos and priority level.'},
                            {'question': 'What\'s the maintenance schedule?', 'answer': 'Monthly system checks, quarterly deep cleaning, annual equipment calibration. All logged in maintenance database.'},
                            {'question': 'How do I request new equipment?', 'answer': 'Submit equipment request with justification and cost estimate. Requires budget approval.'},
                        ]
                    }
                ]
            }
        ]

class ContactView(TemplateView):
    template_name = 'website/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import ContactForm
        context['form'] = ContactForm()
        return context

    def post(self, request, *args, **kwargs):
        from .forms import ContactForm
        from .models import NewsletterSubscriber, ContactMessage
        from django.contrib import messages
        from django.shortcuts import redirect
        import logging

        logger = logging.getLogger(__name__)

        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the contact message
            contact_message = form.save(commit=False)

            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                contact_message.ip_address = x_forwarded_for.split(',')[0]
            else:
                contact_message.ip_address = request.META.get('REMOTE_ADDR')

            # Ensure the newsletter subscription preference is saved
            subscribe_newsletter = form.cleaned_data.get('subscribe_newsletter', False)
            contact_message.subscribe_newsletter = subscribe_newsletter
            contact_message.save()

            logger.info(f"Contact form submitted - Email: {contact_message.email}, Newsletter: {subscribe_newsletter}")

            # Handle newsletter subscription
            if subscribe_newsletter:
                email = form.cleaned_data['email']
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']

                try:
                    # Check if already subscribed
                    existing_subscriber = NewsletterSubscriber.objects.filter(email=email).first()
                    if not existing_subscriber:
                        subscriber = NewsletterSubscriber.objects.create(
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            is_active=True,
                            subscription_source='contact_form'
                        )
                        # Send welcome email for new subscriptions
                        from .email_utils import EmailService
                        EmailService.send_newsletter_welcome(subscriber)
                        logger.info(f"Newsletter subscriber created and welcome email sent: {email}")
                        messages.success(request, 'Thank you! Your message has been sent and you\'ve been subscribed to our newsletter.')
                    else:
                        # Check if they were previously unsubscribed and want to resubscribe
                        if not existing_subscriber.is_active:
                            existing_subscriber.is_active = True
                            existing_subscriber.unsubscribed_at = None
                            existing_subscriber.save()
                            # Send welcome email for reactivations
                            from .email_utils import EmailService
                            EmailService.send_newsletter_welcome(existing_subscriber)
                            logger.info(f"Newsletter subscriber reactivated and welcome email sent: {email}")
                            messages.success(request, 'Welcome back! Your newsletter subscription has been reactivated.')
                        else:
                            logger.info(f"Newsletter subscriber already active: {email}")
                            messages.success(request, 'Thank you! Your message has been sent. You\'re already subscribed to our newsletter.')
                except Exception as e:
                    logger.error(f"Failed to create newsletter subscriber: {e}")
                    messages.success(request, 'Thank you! Your message has been sent. (Note: Newsletter subscription failed, but your message was received.)')
            else:
                messages.success(request, 'Thank you! Your message has been sent.')

            return redirect('core:contact')
        else:
            logger.warning(f"Contact form validation failed: {form.errors}")
            context = self.get_context_data(**kwargs)
            context['form'] = form
        """Get user notifications"""
        notifications = Notification.objects.filter(user=request.user)[:10]

        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'category': notification.category,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'link_url': notification.link_url,
                'link_text': notification.link_text,
            })

        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return JsonResponse({
            'notifications': data,
            'unread_count': unread_count,
        })

@method_decorator(login_required, name='dispatch')
class MarkNotificationReadView(View):
    """Mark notification as read"""

    def post(self, request, notification_id):
        try:
            notification = get_object_or_404(
                Notification,
                id=notification_id, 
                user=request.user
            )
            notification.mark_as_read()

            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@method_decorator(login_required, name='dispatch')
class MarkAllNotificationsReadView(View):
    """Mark all notifications as read"""

    def post(self, request):
        try:
            Notification.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())

            return JsonResponse({
                'success': True,
                'message': 'All notifications marked as read'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

class NotificationListView(LoginRequiredMixin, ListView):
    """View for displaying user notifications"""
    model = Notification
    template_name = 'core/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        return context

class NotificationAPIView(LoginRequiredMixin, View):
    """API endpoint for user notifications"""

    def get(self, request):
        """Get user notifications"""
        notifications = Notification.objects.filter(user=request.user)[:10]

        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'category': notification.category,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'link_url': notification.link_url,
                'link_text': notification.link_text,
            })

        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return JsonResponse({
            'notifications': data,
            'unread_count': unread_count,
        })

class NewsletterSubscribeView(View):
    """Handle newsletter subscription"""

    def post(self, request):
        from .newsletter_service import NewsletterService
        import logging

        logger = logging.getLogger(__name__)

        try:
            email = request.POST.get('email')
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': 'Email address is required.'
                }, status=400)

            # Use the newsletter service to handle subscription (including resubscription)
            service = NewsletterService()
            result = service.subscribe_email(
                email=email,
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                source='newsletter_form'
            )

            if result['success']:
                logger.info(f"Newsletter subscription successful for: {email}")
                return JsonResponse({
                    'success': True,
                    'message': result['message'],
                    'is_new': result.get('is_new', False),
                    'was_reactivated': result.get('was_reactivated', False)
                })
            else:
                logger.warning(f"Newsletter subscription failed for: {email} - {result.get('error', 'Unknown error')}")
                return JsonResponse({
                    'success': False,
                    'message': result.get('error', 'Subscription failed. Please try again.')
                }, status=400)

        except Exception as e:
            logger.error(f"Newsletter subscription failed: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Subscription failed. Please try again.'
            }, status=500)

class NotificationTestView(LoginRequiredMixin, View):
    """Test notification creation and email sending"""

    def get(self, request):
        # Create a test notification
        from .models import Notification
        from .email_utils import EmailService

        try:
            # Create notification
            notification = Notification.create_notification(
                user=request.user,
                title='Test Notification',
                message='This is a test notification to verify the system is working.',
                notification_type='info',
                category='system',
                send_email=True
            )
            
            # Also send a direct email test
            EmailService.send_admin_notification(
                subject='Test Notification System',
                message='This is a test email from the Olivian Group notification system.',
                user=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Test notification created and email sent successfully!',
                'notification_id': notification.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)


class LegalDocumentView(TemplateView):
    """Display legal documents like Privacy Policy and Terms of Service"""
    template_name = 'website/legal_document.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc_type = kwargs.get('doc_type')
        
        # Get the requested legal document
        document = get_object_or_404(
            LegalDocument, 
            document_type=doc_type, 
            is_active=True
        )
        
        company = CompanySettings.get_settings()
        context.update({
            'document': document,
            'page_title': document.title,
            'meta_description': document.short_description or f'{document.title} - {company.name}'
        })
        
        return context


class PrivacyPolicyView(TemplateView):
    """Dedicated Privacy Policy view"""
    template_name = 'website/legal_document.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        document = LegalDocument.get_privacy_policy()
        if not document:
            # Create a basic privacy policy if none exists
            document = LegalDocument(
                document_type='privacy_policy',
                title='Privacy Policy',
                content='<p>Privacy Policy content will be added here.</p>',
                is_active=False
            )
        
        try:
            company = CompanySettings.get_settings()
            company_name = company.name
        except:
            company_name = "Olivian Group"
            
        context.update({
            'document': document,
            'page_title': 'Privacy Policy',
            'meta_description': f'Privacy Policy - {company_name}'
        })
        
        return context


class TermsOfServiceView(TemplateView):
    """Dedicated Terms of Service view"""
    template_name = 'website/legal_document.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document = LegalDocument.get_terms_of_service()
        if not document:
            # Create a basic terms of service if none exists
            document = LegalDocument(
                document_type='terms_of_service',
                title='Terms of Service',
                content='<p>Terms of Service content will be added here.</p>',
                is_active=False
            )

        try:
            company = CompanySettings.get_settings()
            company_name = company.name
        except:
            company_name = "Olivian Group"

        context.update({
            'document': document,
            'page_title': 'Terms of Service',
            'meta_description': f'Terms of Service - {company_name}'
        })

        return context


class DataDeletionView(TemplateView):
    """Dedicated Data Deletion view"""
    template_name = 'website/legal_document.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document = LegalDocument.get_data_deletion()
        if not document:
            # Fallback content if document doesn't exist
            document = type('LegalDocument', (), {
                'document_type': 'data_deletion',
                'title': 'How to Delete Your Data',
                'content': '<p>Data deletion document is being prepared. Please check back later.</p>',
                'short_description': 'Learn how to request deletion of your personal data from our systems.',
                'version': '1.0',
                'is_active': True,
                'effective_date': timezone.now().date(),
            })()

        try:
            company = CompanySettings.get_settings()
            company_name = company.name
        except:
            company_name = "Olivian Group"

        context.update({
            'document': document,
            'page_title': 'How to Delete Your Data',
            'meta_description': f'Data deletion instructions - Learn how to request deletion of your data from {company_name}'
        })

        return context


class DisclaimerView(TemplateView):
    """Dedicated Disclaimer view"""
    template_name = 'website/legal_document.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document = LegalDocument.get_disclaimer()
        if not document:
            # Fallback content if document doesn't exist
            document = type('LegalDocument', (), {
                'document_type': 'disclaimer',
                'title': 'Website Disclaimer',
                'content': '<p>Disclaimer document is being prepared. Please check back later.</p>',
                'short_description': 'Important legal notices and limitations regarding our website and services.',
                'version': '1.0',
                'is_active': True,
                'effective_date': timezone.now().date(),
            })()

        try:
            company = CompanySettings.get_settings()
            company_name = company.name
        except:
            company_name = "Olivian Group"

        context.update({
            'document': document,
            'page_title': 'Website Disclaimer',
            'meta_description': f'Disclaimer - Important legal notices for {company_name}'
        })

        return context


class RefundPolicyView(TemplateView):
    """Dedicated Refund Policy view"""
    template_name = 'website/legal_document.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document = LegalDocument.get_refund_policy()
        if not document:
            # Fallback content if document doesn't exist
            document = type('LegalDocument', (), {
                'document_type': 'refund_policy',
                'title': 'Refund Policy',
                'content': '<p>Refund policy document is being prepared. Please check back later.</p>',
                'short_description': 'Learn about our refund policy for products and services.',
                'version': '1.0',
                'is_active': True,
                'effective_date': timezone.now().date(),
            })()

        try:
            company = CompanySettings.get_settings()
            company_name = company.name
        except:
            company_name = "Olivian Group"

        context.update({
            'document': document,
            'page_title': 'Refund Policy',
            'meta_description': f'Refund policy for {company_name} products and services'
        })


        return context


# Cookie Management Views

def get_client_identifier(request):
    """Generate unique identifier for anonymous users"""
    ip = request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return hashlib.sha256(f"{ip}{user_agent}".encode()).hexdigest()


@never_cache
def cookie_consent_status(request):
    """API endpoint to get current cookie consent status"""
    user = request.user if request.user.is_authenticated else None
    identifier = get_client_identifier(request) if not user else None
    
    try:
        if user:
            consent = CookieConsent.objects.get(user=user)
        else:
            consent = CookieConsent.objects.get(identifier=identifier)
            
        return JsonResponse({
            'has_consent': True,
            'essential': consent.essential_consent,
            'analytics': consent.analytics_consent,
            'marketing': consent.marketing_consent,
            'preferences': consent.preferences_consent,
            'social': consent.social_consent,
            'consent_date': consent.consent_date.isoformat(),
        })
    except CookieConsent.DoesNotExist:
        return JsonResponse({
            'has_consent': False,
            'essential': 'pending',
            'analytics': 'pending',
            'marketing': 'pending',
            'preferences': 'pending',
            'social': 'pending',
        })


@require_POST
@never_cache
def update_cookie_consent(request):
    """API endpoint to update cookie consent preferences"""
    try:
        data = json.loads(request.body)
        
        user = request.user if request.user.is_authenticated else None
        identifier = get_client_identifier(request) if not user else None
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Get or create consent record
        consent, created = CookieConsent.get_or_create_consent(
            user=user,
            identifier=identifier,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update consent preferences
        consent.essential_consent = data.get('essential', 'granted')  # Always granted
        consent.analytics_consent = data.get('analytics', 'denied')
        consent.marketing_consent = data.get('marketing', 'denied')
        consent.preferences_consent = data.get('preferences', 'denied')
        consent.social_consent = data.get('social', 'denied')
        consent.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cookie preferences updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating cookie preferences: {str(e)}'
        }, status=500)


class CookiePreferencesView(TemplateView):
    """View for cookie preferences page"""
    template_name = 'core/cookie_preferences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cookie categories
        categories = CookieCategory.objects.filter(is_active=True)
        
        # Get current consent status
        user = self.request.user if self.request.user.is_authenticated else None
        identifier = get_client_identifier(self.request) if not user else None
        
        current_consent = None
        try:
            if user:
                current_consent = CookieConsent.objects.get(user=user)
            elif identifier:
                current_consent = CookieConsent.objects.get(identifier=identifier)
        except CookieConsent.DoesNotExist:
            pass
        
        context.update({
            'categories': categories,
            'current_consent': current_consent,
            'page_title': 'Cookie Preferences',
            'meta_description': 'Manage your cookie preferences and privacy settings.'
        })
        
        return context


@never_cache
def cookie_categories_api(request):
    """API endpoint to get cookie categories and details"""
    categories = CookieCategory.objects.filter(is_active=True).prefetch_related('cookies')
    
    data = []
    for category in categories:
        category_data = {
            'name': category.name,
            'display_name': category.display_name,
            'description': category.description,
            'is_essential': category.is_essential,
            'cookies': [
                {
                    'name': cookie.name,
                    'purpose': cookie.purpose,
                    'duration': cookie.duration,
                    'third_party': cookie.third_party,
                    'provider': cookie.provider,
                }
                for cookie in category.cookies.filter(is_active=True)
            ]
        }
        data.append(category_data)
    
    return JsonResponse({'categories': data})


class CookiePolicyView(TemplateView):
    """Enhanced cookie policy view with interactive features"""
    template_name = 'core/cookie_policy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cookie policy document
        document = LegalDocument.objects.filter(
            document_type='cookie_policy', 
            is_active=True
        ).first()
        
        # Get cookie categories for detailed breakdown
        categories = CookieCategory.objects.filter(is_active=True).prefetch_related('cookies')
        
        # Company info
        try:
            company = CompanySettings.objects.first()
            company_name = company.name if company else "Olivian Group"
        except:
            company_name = "Olivian Group"
            
        context.update({
            'document': document,
            'categories': categories,
            'page_title': 'Cookie Policy',
            'meta_description': f'Cookie Policy - Learn how {company_name} uses cookies'
        })
        
        return context


class SystemAdminRequiredMixin(UserPassesTestMixin):
    """Verify that the current user is a system administrator"""
    
    def test_func(self):
        return (self.request.user.is_authenticated and 
                self.request.user.is_staff and 
                self.request.user.role == 'super_admin')  # Changed from 'admin' to 'super_admin'
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to access this feature.')
            return redirect('accounts:login')
        else:
            messages.error(self.request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')

@method_decorator(csrf_exempt, name='dispatch')
class SystemBackupView(SystemAdminRequiredMixin, View):
    """Create system backup including database and media files"""
    
    CHUNK_SIZE = 8192
    
    def get(self, request):
        """Handle GET request for backup creation"""
        try:
            temp_dir = tempfile.mkdtemp()
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'olivian_backup_{timestamp}'
            
            response = StreamingHttpResponse(
                self.generate_backup(backup_name),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="{backup_name}.zip"'
            return response
            
        except Exception as e:
            logger.error(f'Backup creation failed: {str(e)}', exc_info=True)
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def http_method_not_allowed(self, request, *args, **kwargs):
        """Handle invalid HTTP methods"""
        logger.warning(f'Invalid method {request.method} attempted for backup')
        return JsonResponse({
            'error': f'Method {request.method} not allowed. Use GET to create backup.'
        }, status=405)

    def generate_backup(self, backup_name):
        """Generator function to stream the backup file"""
        temp_dir = tempfile.mkdtemp()
        temp_sql = None
        zip_path = None

        try:
            # Ensure backup directory exists
            if not os.path.exists(settings.BACKUP_ROOT):
                os.makedirs(settings.BACKUP_ROOT)

            zip_path = os.path.join(settings.BACKUP_ROOT, f'{backup_name}.zip')

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Create temporary SQL file
                temp_sql = os.path.join(temp_dir, 'database_backup.sql')

                # Backup database to temp file
                self.backup_database(temp_sql)

                # Add SQL file to zip
                backup_zip.write(temp_sql, 'database_backup.sql')

                # Backup media files
                self.backup_media_files(backup_zip)

                # Backup system configuration
                self.backup_system_config(backup_zip)

            # Update last backup timestamp on successful creation
            try:
                company_settings = CompanySettings.get_settings()
                company_settings.last_backup_datetime = timezone.now()
                company_settings.save(update_fields=['last_backup_datetime'])
                logger.info('Last backup timestamp updated successfully')
            except Exception as e:
                logger.error(f'Failed to update last backup timestamp: {str(e)}')
                # Don't fail the backup if timestamp update fails

            # Stream the zip file in chunks
            with open(zip_path, 'rb') as f:
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk

        finally:
            # Clean up temporary files
            if temp_sql and os.path.exists(temp_sql):
                try:
                    os.unlink(temp_sql)
                except Exception as e:
                    logger.warning(f'Failed to delete temp SQL file: {str(e)}')

            # Remove temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f'Failed to remove temp directory: {str(e)}')

    def backup_database(self, temp_sql_path):
        """Create database backup using mysqldump"""
        try:
            db_settings = settings.DATABASES['default']
            mysqldump_cmd = [
                'mysqldump',
                '--host=' + db_settings.get('HOST', 'localhost'),
                '--port=' + str(db_settings.get('PORT', 3306)),
                '--user=' + db_settings['USER'],
                f"--password={db_settings['PASSWORD']}",
                '--single-transaction',
                '--quick',
                '--routines',
                '--triggers',
                '--events',
                '--set-charset',
                '--skip-lock-tables',
                db_settings['NAME']
            ]

            with open(temp_sql_path, 'w') as f:
                subprocess.run(mysqldump_cmd, stdout=f, check=True)
            logger.info('Database backup completed successfully')
            
        except Exception as e:
            logger.error(f'Database backup failed: {str(e)}')
            raise

    def backup_media_files(self, backup_zip):
        """Backup media files in chunks"""
        try:
            media_root = str(settings.MEDIA_ROOT)  # Convert to string
            backup_dir = str(settings.BACKUP_ROOT)  # Convert to string
            
            if os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    # Skip the backup directory
                    if backup_dir in str(root):  # Convert root to string for comparison
                        continue
                        
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            # Skip files larger than 100MB
                            if os.path.getsize(file_path) > 100 * 1024 * 1024:
                                logger.warning(f'Skipping large file: {file_path}')
                                continue
                                
                            # Get relative path for ZIP
                            arcname = os.path.join('media', 
                                     os.path.relpath(file_path, media_root))
                            
                            # Skip backup files
                            if 'backup' in arcname.lower():
                                continue
                                
                            backup_zip.write(file_path, arcname)
                            
                        except Exception as e:
                            logger.warning(f'Failed to backup file {file_path}: {str(e)}')
                            continue
                    
                logger.info('Media files backup completed successfully')
                
            else:
                logger.warning('Media root directory does not exist')
                
        except Exception as e:
            logger.error(f'Media files backup failed: {str(e)}')
            raise

    def backup_system_config(self, backup_zip):
        """Backup system configuration files"""
        try:
            # Backup settings files
            settings_dir = os.path.join(settings.BASE_DIR, 'olivian_solar')
            config_files = [
                'settings.py',
                'local_settings.py',
                '.env'
            ]
            
            for file in config_files:
                file_path = os.path.join(settings_dir, file)
                if os.path.exists(file_path):
                    backup_zip.write(file_path, 
                                   os.path.join('config', file))
            
            logger.info('System configuration backup completed successfully')
            
        except Exception as e:
            logger.error(f'System configuration backup failed: {str(e)}')
            raise

class SystemMaintenanceView(SystemAdminRequiredMixin, TemplateView):
    """System maintenance dashboard"""
    template_name = 'core/system_maintenance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get database size for MySQL
            from django.db import connection
            with connection.cursor() as cursor:
                # Get the database name from settings
                db_name = connection.settings_dict['NAME']
                
                # MySQL query to get database size
                cursor.execute("""
                    SELECT 
                        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    GROUP BY table_schema
                """, [db_name])
                result = cursor.fetchone()
                db_size = result[0] if result else 0
                
            # Calculate media directory size
            media_size = 0
            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                media_size += sum(os.path.getsize(os.path.join(root, name)) 
                                for name in files)
            
            # Run system checks
            system_checks = self.run_system_checks()
            
            # Get disk information
            disk = psutil.disk_usage('/')
            disk_details = {
                'total_gb': round(disk.total / (1024**3), 1),
                'used_gb': round(disk.used / (1024**3), 1),
                'available_gb': round(disk.free / (1024**3), 1),
                'usage_percent': disk.percent
            }

            # Format sizes for display
            context.update({
                'db_size_mb': round(db_size, 2),
                'db_size_gb': round(db_size / 1024, 2),
                'media_size_mb': round(media_size / (1024 * 1024), 2),
                'media_size_gb': round(media_size / (1024 * 1024 * 1024), 2),
                'disk_used_gb': disk_details['used_gb'],
                'disk_total_gb': disk_details['total_gb'],
                'disk_usage_percent': disk_details['usage_percent'],
                'python_version': platform.python_version(),
                'django_version': django.get_version(),
                'mysql_version': self.get_mysql_version(),
                'last_backup': self.get_last_backup_date(),
                'system_checks': system_checks,
                'system_info': self.get_system_info(),
            })
            
        except Exception as e:
            logger.error(f'Error in system maintenance view: {str(e)}')
            context.update({
                'error_message': str(e),
                'db_size_mb': 0,
                'db_size_gb': 0,
                'media_size_mb': 0,
                'media_size_gb': 0,
                'system_checks': [],
            })
        
        return context
    
    def get_mysql_version(self):
        """Get MySQL server version"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                return cursor.fetchone()[0]
        except:
            return 'Unknown'
    
    def get_last_backup_date(self):
        """Get date of last system backup"""
        try:
            # First check CompanySettings for the persistent timestamp
            company_settings = CompanySettings.get_settings()
            if company_settings.last_backup_datetime:
                return company_settings.last_backup_datetime

            # Fallback to file timestamps if no database record exists
            backup_dir = settings.BACKUP_ROOT
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                return None

            # Get list of backup files
            backup_files = []
            for f in os.listdir(backup_dir):
                if f.startswith('olivian_backup_'):
                    file_path = os.path.join(backup_dir, f)
                    if os.path.isfile(file_path):
                        # Get file creation/modification time
                        timestamp = os.path.getmtime(file_path)
                        backup_files.append((f, timestamp))

            if not backup_files:
                return None

            # Get most recent backup based on file timestamp
            latest_backup = max(backup_files, key=lambda x: x[1])
            return datetime.fromtimestamp(latest_backup[1])

        except Exception as e:
            logger.error(f'Error getting last backup date: {str(e)}')
            return None
    
    def run_system_checks(self):
        """Run various system health checks"""
        checks = []

        try:
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                checks.append({
                    'name': 'Disk Space',
                    'status': 'critical',
                    'message': f'Disk usage is at {disk.percent}%'
                })
            elif disk.percent > 75:
                checks.append({
                    'name': 'Disk Space',
                    'status': 'warning',
                    'message': f'Disk usage is at {disk.percent}%'
                })
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                checks.append({
                    'name': 'Memory',
                    'status': 'critical',
                    'message': f'Memory usage is at {memory.percent}%'
                })
            elif memory.percent > 75:
                checks.append({
                    'name': 'Memory',
                    'status': 'warning',
                    'message': f'Memory usage is at {memory.percent}%'
                })
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                checks.append({
                    'name': 'CPU',
                    'status': 'critical',
                    'message': f'CPU usage is at {cpu_percent}%'
                })
            elif cpu_percent > 75:
                checks.append({
                    'name': 'CPU',
                    'status': 'warning',
                    'message': f'CPU usage is at {cpu_percent}%'
                })
            
            # Check MySQL connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks.append({
                    'name': 'Database',
                    'status': 'healthy',
                    'message': 'Database connection is working'
                })
            
            # Check media directory
            if os.path.exists(settings.MEDIA_ROOT):
                checks.append({
                    'name': 'Media Directory',
                    'status': 'healthy',
                    'message': 'Media directory is accessible'
                })
            else:
                checks.append({
                    'name': 'Media Directory',
                    'status': 'critical',
                    'message': 'Media directory is not accessible'
                })
            
        except Exception as e:
            checks.append({
                'name': 'System Check',
                'status': 'error',
                'message': f'Error running system checks: {str(e)}'
            })
        
        return checks
    
    def get_system_info(self):
        """Get general system information with error handling"""
        info = {}
        try:
            info.update({
                'platform': platform.platform(),
                'processor': platform.processor() or 'Unknown',
                'architecture': platform.architecture()[0],
                'python_path': sys.executable,
                'python_version': sys.version,
                'timezone': settings.TIME_ZONE,
                'encoding': sys.getdefaultencoding(),
            })

            # Database information - wrapped in try block
            try:
                info.update({
                    'mysql_host': settings.DATABASES['default'].get('HOST', 'localhost'),
                    'mysql_port': settings.DATABASES['default'].get('PORT', '3306'),
                    'database_name': settings.DATABASES['default'].get('NAME', 'unknown'),
                    'database_engine': settings.DATABASES['default'].get('ENGINE', '').split('.')[-1],
                })
            except Exception as db_error:
                logger.warning(f'Error getting database info: {str(db_error)}')
                info.update({
                    'mysql_host': 'Error retrieving',
                    'mysql_port': 'Error retrieving',
                    'database_name': 'Error retrieving',
                    'database_engine': 'Error retrieving',
                })

            # System resources - wrapped in try block
            try:
                memory = psutil.virtual_memory()
                info.update({
                    'total_memory': f"{memory.total / (1024**3):.1f} GB",
                    'cpu_cores': psutil.cpu_count(logical=False),
                    'cpu_threads': psutil.cpu_count(logical=True),
                })
            except Exception as sys_error:
                logger.warning(f'Error getting system resources: {str(sys_error)}')
                info.update({
                    'total_memory': 'Error retrieving',
                    'cpu_cores': 'Error retrieving',
                    'cpu_threads': 'Error retrieving',
                })

        except Exception as e:
            logger.error(f'Error getting system info: {str(e)}')
            info = {
                'error': 'Error retrieving system information',
                'error_details': str(e)
            }
        
        return info


class SystemHealthView(LoginRequiredMixin, View):
    """Simple API endpoint for system health checks"""

    def get(self, request):
        try:
            # Basic system health check
            status = 'healthy'
            message = 'All systems operational'

            # Check database connectivity
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Check for critical levels
            alerts = []
            if cpu_percent > 90:
                status = 'critical'
                alerts.append(f'CPU usage critically high at {cpu_percent}%')
            elif cpu_percent > 75:
                status = 'warning'
                alerts.append(f'CPU usage high at {cpu_percent}%')

            if memory.percent > 90:
                status = 'critical'
                alerts.append(f'Memory usage critically high at {memory.percent}%')
            elif memory.percent > 75:
                status = 'warning'
                alerts.append(f'Memory usage high at {memory.percent}%')

            return JsonResponse({
                'status': status,
                'message': message if status == 'healthy' else f'{len(alerts)} system alert(s) detected',
                'alerts': alerts,
                'metrics': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'timestamp': timezone.now().isoformat()
                }
            })

        except Exception as e:
            logger.error(f'System health check failed: {str(e)}')
            return JsonResponse({
                'status': 'error',
                'message': 'System health check failed',
                'error': str(e)
            }, status=500)


class SystemReportsView(SystemAdminRequiredMixin, TemplateView):
    """System-wide reports dashboard"""
    template_name = 'core/system_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Convert string dates to datetime objects
        try:
            start_date = datetime.strptime(
                self.request.GET.get('start_date', ''), 
                '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            start_date = (timezone.now() - timezone.timedelta(days=30)).date()
            
        try:
            end_date = datetime.strptime(
                self.request.GET.get('end_date', ''), 
                '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            end_date = timezone.now().date()
        
        # Generate reports
        context.update({
            'user_stats': self.get_user_statistics(start_date, end_date),
            'system_stats': self.get_system_statistics(start_date, end_date),
            'financial_stats': self.get_financial_statistics(start_date, end_date),
        })
        return context
    
    def get_user_statistics(self, start_date, end_date):
        """Get user statistics for the given date range"""
        try:
            # Get all users with their last activity
            users = User.objects.annotate(
                last_activity=Max('activitylog__created_at')
            )
            
            total_users = users.count()
            
            # New users in date range
            new_users = users.filter(
                date_joined__date__range=[start_date, end_date]
            ).count()
            
            # Active users (activity in last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            active_users = users.filter(
                Q(last_login__gte=thirty_days_ago) |
                Q(last_activity__gte=thirty_days_ago)
            ).count()
            
            # Inactive users (no activity in last 30 days)
            inactive_users = users.filter(
                Q(last_login__lt=thirty_days_ago) | Q(last_login__isnull=True),
                Q(last_activity__lt=thirty_days_ago) | Q(last_activity__isnull=True)
            ).count()
            
            # Role distribution
            role_distribution = users.values('role').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Most active users
            most_active = users.filter(
                Q(last_login__gte=thirty_days_ago) |
                Q(last_activity__gte=thirty_days_ago)
            ).order_by('-last_activity')[:5]
            
            return {
                'total_users': total_users,
                'new_users': new_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'role_distribution': {
                    item['role']: item['count'] 
                    for item in role_distribution
                },
                'most_active_users': [
                    {
                        'username': user.username,
                        'last_activity': user.last_activity or user.last_login
                    }
                    for user in most_active if user.last_activity or user.last_login
                ]
            }
            
        except Exception as e:
            logger.error(f'Error getting user statistics: {str(e)}')
            return None
    
    def get_system_statistics(self, start_date, end_date):
        """Get system statistics for the given date range"""
        try:
            # Get real-time metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get historical averages from ActivityLog
            system_logs = ActivityLog.objects.filter(
                created_at__date__range=[start_date, end_date],
                log_type='system'
            )
            
            cpu_logs = system_logs.filter(metric='cpu_usage')
            memory_logs = system_logs.filter(metric='memory_usage')
            
            avg_cpu_usage = cpu_logs.aggregate(Avg('value'))['value__avg'] or cpu_percent
            avg_memory_usage = memory_logs.aggregate(Avg('value'))['value__avg'] or memory.percent
            
            # Calculate system uptime
            boot_time = psutil.boot_time()
            uptime_seconds = timezone.now().timestamp() - boot_time
            uptime_days = int(uptime_seconds / (24 * 3600))
            uptime_hours = int((uptime_seconds % (24 * 3600)) / 3600)
            
            # Calculate account-specific disk usage
            account_disk_gb = self.get_account_disk_usage()

            return {
                'current_cpu_usage': cpu_percent,
                'current_memory_usage': memory.percent,
                'avg_cpu_usage': round(avg_cpu_usage, 1),
                'avg_memory_usage': round(avg_memory_usage, 1),
                'disk_usage': disk.percent,
                'uptime': f'{uptime_days} days, {uptime_hours} hours',
                'memory_details': {
                    'total': f'{memory.total / (1024**3):.1f} GB',
                    'available': f'{memory.available / (1024**3):.1f} GB',
                    'used': f'{memory.used / (1024**3):.1f} GB'
                },
                'disk_details': {
                    'total': f'{disk.total / (1024**3):.1f} GB',
                    'available': f'{disk.free / (1024**3):.1f} GB',
                    'used': f'{disk.used / (1024**3):.1f} GB'
                },
                'account_disk_usage': f'{account_disk_gb:.1f} GB'
            }
            
        except Exception as e:
            logger.error(f'Error getting system statistics: {str(e)}')
            return None
    
    def get_account_disk_usage(self):
        """Calculate account-specific disk usage by summing files in project and media directories"""
        total_size = 0
        paths = [str(settings.MEDIA_ROOT), str(settings.BASE_DIR)]
        for path in paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        try:
                            fp = os.path.join(root, file)
                            total_size += os.path.getsize(fp)
                        except (OSError, IOError):
                            pass
        return total_size / (1024**3)  # Convert to GB

    def get_financial_statistics(self, start_date, end_date):
        """Get financial statistics for the given date range"""
        try:
            # Get transactions based on the Transaction model fields
            current_revenue = Transaction.objects.filter(
                transaction_type__in=['deposit', 'payment', 'receipt'],
                transaction_date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            current_expenses = Transaction.objects.filter(
                transaction_type__in=['withdrawal', 'fee', 'payment'],
                transaction_date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate previous period
            days_diff = (end_date - start_date).days
            prev_start = start_date - timezone.timedelta(days=days_diff)
            prev_end = start_date - timezone.timedelta(days=1)
            
            prev_revenue = Transaction.objects.filter(
                transaction_type__in=['deposit', 'payment', 'receipt'],
                transaction_date__range=[prev_start, prev_end]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            prev_expenses = Transaction.objects.filter(
                transaction_type__in=['withdrawal', 'fee', 'payment'],
                transaction_date__range=[prev_start, prev_end]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate changes and profit
            revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
            expenses_change = ((current_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses else 0
            
            current_profit = current_revenue - current_expenses
            prev_profit = prev_revenue - prev_expenses
            profit_change = ((current_profit - prev_profit) / prev_profit * 100) if prev_profit else 0
            
            # Log the statistics for debugging
            logger.info(f"""
                Financial Statistics:
                Period: {start_date} to {end_date}
                Revenue: {current_revenue}
                Expenses: {current_expenses}
                Profit: {current_profit}
                Changes: Revenue {revenue_change}%, Expenses {expenses_change}%, Profit {profit_change}%
            """)
            
            return {
                'total_revenue': current_revenue,
                'total_expenses': current_expenses,
                'net_profit': current_profit,
                'revenue_change': round(revenue_change, 1),
                'expenses_change': round(expenses_change, 1),
                'profit_change': round(profit_change, 1),
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'days': days_diff
                },
                'transaction_counts': {
                    'revenue': Transaction.objects.filter(
                        transaction_type__in=['deposit', 'payment', 'receipt'],
                        transaction_date__range=[start_date, end_date]
                    ).count(),
                    'expense': Transaction.objects.filter(
                        transaction_type__in=['withdrawal', 'fee', 'payment'],
                        transaction_date__range=[start_date, end_date]
                    ).count()
                }
            }
            
        except Exception as e:
            logger.error(f'Error getting financial statistics: {str(e)}', exc_info=True)
            return {
                'total_revenue': 0,
                'total_expenses': 0,
                'net_profit': 0,
                'revenue_change': 0,
                'expenses_change': 0,
                'profit_change': 0,
                'error': str(e)
            }

class SystemLogsView(SystemAdminRequiredMixin, ListView):
    """Display system logs with filtering"""
    template_name = 'core/system_logs.html'
    model = ActivityLog
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        log_type = self.request.GET.get('type')
        if log_type:
            queryset = queryset.filter(log_type=log_type)
            
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(message__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(ip_address__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['log_types'] = ActivityLog.LOG_TYPES
        context['severity_levels'] = ActivityLog.SEVERITY_LEVELS
        return context

class ExportAllDataView(SystemAdminRequiredMixin, View):
    """Export all system data in JSON format"""
    
    def get(self, request):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'olivian_data_export_{timestamp}.json'
                filepath = os.path.join(temp_dir, filename)
                
                # Export all data excluding problematic tables
                with open(filepath, 'w') as f:
                    call_command('dumpdata', 
                               exclude=[
                                   'auth.permission',
                                   'sessions',
                                   'admin.logentry',
                                   'core.bankaccount',  # Exclude non-existent model
                                   'contenttypes'
                               ],
                               natural_foreign=True,
                               indent=2,
                               output=filepath)
                
                # Send file to user
                with open(filepath, 'rb') as f:
                    response = HttpResponse(f.read(), 
                                         content_type='application/json')
                    response['Content-Disposition'] = \
                        f'attachment; filename="{filename}"'
                
                logger.info(f'Full data export created by {request.user.username}')
                return response
                
        except Exception as e:
            logger.error(f'Data export failed: {str(e)}', exc_info=True)
            messages.error(request, f'Data export failed: {str(e)}')
            return redirect('core:system_reports')

class ExportUserReportView(SystemAdminRequiredMixin, View):
    """Export detailed user report in CSV format"""
    
    def get(self, request):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'user_report_{timestamp}.csv'
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            # Updated headers to match available fields
            writer.writerow([
                'Username', 
                'Email', 
                'Role', 
                'Date Joined', 
                'Last Login', 
                'Status', 
                'Last Activity'
            ])
            
            # Remove select_related('department') as it doesn't exist
            users = User.objects.all().select_related('userprofile')
            for user in users:
                writer.writerow([
                    user.username,
                    user.email,
                    user.role,
                    user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                    'Active' if user.is_active else 'Inactive',
                    user.last_activity.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'last_activity') else 'N/A'
                ])
            
            return response
            
        except Exception as e:
            logger.error(f'User report export failed: {str(e)}', exc_info=True)
            messages.error(request, f'User report export failed: {str(e)}')
            return redirect('core:system_reports')

class ExportSystemReportView(SystemAdminRequiredMixin, View):
    """Export system health and performance report"""
    
    def get(self, request):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'system_report_{timestamp}.csv'
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # System Overview
            writer.writerow(['System Overview'])
            writer.writerow(['Metric', 'Value'])
            
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = psutil.boot_time()
            uptime_seconds = timezone.now().timestamp() - boot_time
            
            writer.writerow(['CPU Usage', f'{cpu_percent}%'])
            writer.writerow(['Memory Usage', f'{memory.percent}%'])
            writer.writerow(['Disk Usage', f'{disk.percent}%'])
            writer.writerow(['Uptime', f'{int(uptime_seconds/86400)} days, {int((uptime_seconds%86400)/3600)} hours'])
            writer.writerow([])
            
            # Memory Details
            writer.writerow(['Memory Details'])
            writer.writerow(['Total Memory', f'{memory.total/1024/1024/1024:.2f} GB'])
            writer.writerow(['Available Memory', f'{memory.available/1024/1024/1024:.2f} GB'])
            writer.writerow(['Used Memory', f'{memory.used/1024/1024/1024:.2f} GB'])
            writer.writerow([])
            
            # Disk Details
            writer.writerow(['Disk Details'])
            writer.writerow(['Total Space', f'{disk.total/1024/1024/1024:.2f} GB'])
            writer.writerow(['Used Space', f'{disk.used/1024/1024/1024:.2f} GB'])
            writer.writerow(['Free Space', f'{disk.free/1024/1024/1024:.2f} GB'])
            writer.writerow([])
            
            # Activity Logs
            writer.writerow(['Recent System Activity'])
            writer.writerow(['Timestamp', 'Type', 'Message'])
            
            recent_logs = ActivityLog.objects.filter(
                log_type='system'
            ).order_by('-created_at')[:50]
            
            for log in recent_logs:
                writer.writerow([
                    log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    log.log_type,
                    log.message
                ])
            
            return response
            
        except Exception as e:
            logger.error(f'System report export failed: {str(e)}', exc_info=True)
            messages.error(request, f'System report export failed: {str(e)}')
            return redirect('core:system_reports')

class ExportFinancialReportView(SystemAdminRequiredMixin, View):
    """Export comprehensive financial report"""
    
    def get(self, request):
        try:
            # Get date range from request or use defaults
            try:
                start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            except (TypeError, ValueError):
                start_date = (timezone.now() - timezone.timedelta(days=30)).date()
                
            try:
                end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
            except (TypeError, ValueError):
                end_date = timezone.now().date()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'financial_report_{timestamp}.csv'
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Summary Section
            writer.writerow(['Financial Report Summary'])
            writer.writerow(['Period:', f'From {start_date} to {end_date}'])
            writer.writerow([])

            # Transaction Summary
            revenue = Transaction.objects.filter(
                transaction_type__in=['deposit', 'payment', 'receipt'],
                transaction_date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            expenses = Transaction.objects.filter(
                transaction_type__in=['withdrawal', 'fee', 'payment'],
                transaction_date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            writer.writerow(['Summary'])
            writer.writerow(['Total Revenue', f'KES {revenue:,.2f}'])
            writer.writerow(['Total Expenses', f'KES {expenses:,.2f}'])
            writer.writerow(['Net Profit/Loss', f'KES {revenue - expenses:,.2f}'])
            writer.writerow([])
            
            # Detailed Transactions
            writer.writerow(['Detailed Transactions'])
            writer.writerow(['Date', 'Type', 'Description', 'Amount', 'Reference'])
            
            transactions = Transaction.objects.filter(
                transaction_date__range=[start_date, end_date]
            ).order_by('transaction_date')
            
            for tx in transactions:
                writer.writerow([
                    tx.transaction_date.strftime('%Y-%m-%d'),
                    tx.transaction_type,
                    tx.description,
                    f'KES {tx.amount:,.2f}',
                    tx.reference
                ])
            
            return response
            
        except Exception as e:
            logger.error(f'Financial report export failed: {str(e)}', exc_info=True)
            messages.error(request, f'Financial report export failed: {str(e)}')
            return redirect('core:system_reports')

class ExportFinancialCSVView(SystemAdminRequiredMixin, View):
    """Export raw financial data in CSV format"""
    
    def get(self, request):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'financial_data_{timestamp}.csv'
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            self.write_financial_data(writer)
            
            return response
            
        except Exception as e:
            logger.error(f'Financial data export failed: {str(e)}')
            messages.error(request, 'Financial data export failed. Please try again.')
            return redirect('core:system_reports')
    
    def write_financial_data(self, writer):
        # Implementation for writing financial data
        pass

class SystemStatusAPIView(LoginRequiredMixin, View):
    """API endpoint for system status metrics"""
    
    def get(self, request):
        try:
            # Get user stats
            total_users = User.objects.count()
            
            # Get revenue stats
            total_revenue = Transaction.objects.filter(
                transaction_type__in=['deposit', 'payment', 'receipt']
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Get order stats - import from ecommerce app
            from apps.ecommerce.models import Order
            total_orders = Order.objects.count()
            
            # Get project stats - import from projects app
            from apps.projects.models import Project
            active_projects = Project.objects.filter(
                status='in_progress'
            ).count()
            
            # Get inventory stats - import from products app instead
            from apps.products.models import Product
            inventory_items = Product.objects.filter(track_quantity=True).count()
            
            # Calculate system uptime
            uptime = psutil.boot_time()
            uptime_seconds = timezone.now().timestamp() - uptime
            uptime_days = uptime_seconds / (24 * 3600)
            system_uptime = min(99.99, (uptime_days / 30) * 100)  # Monthly uptime percentage
            
            return JsonResponse({
                'total_users': total_users,
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'active_projects': active_projects,
                'inventory_items': inventory_items,
                'system_uptime': round(system_uptime, 2),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f'Error fetching system status: {str(e)}', exc_info=True)
            return JsonResponse({
                'error': 'Failed to fetch system status'
            }, status=500)

class SystemHealthCheckAPIView(LoginRequiredMixin, View):
    """API endpoint for detailed system health checks"""
    
    def get(self, request):
        try:
            # Get detailed CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            cpu_stats = psutil.cpu_stats()
            per_cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            
            # Get detailed memory information
            memory = psutil.virtual_memory()
            try:
                swap = psutil.swap_memory()
            except Exception:
                # Fallback when swap memory stats are not available
                swap = type('swap', (), {'used': 0, 'free': 0, 'total': 0})()

            # Get detailed disk information
            disk = psutil.disk_usage('/')
            try:
                disk_io = psutil.disk_io_counters()
            except Exception:
                # Fallback when disk I/O counters are not available
                disk_io = type('disk_io', (), {'read_bytes': 0, 'write_bytes': 0})()
            
            # Get process information
            process_count = len(psutil.pids())
            python_process = psutil.Process()
            python_memory = python_process.memory_info()
            
            # Calculate load averages
            if hasattr(os, 'getloadavg'):  # Unix systems only
                load1, load5, load15 = os.getloadavg()
            else:
                load1 = load5 = load15 = 0
            
            # Determine status and detailed message
            status = 'healthy'
            alerts = []
            
            # CPU checks
            if cpu_percent > 90:
                status = 'critical'
                alerts.append({
                    'component': 'CPU',
                    'status': 'critical',
                        'message': f'CPU usage critically high at {cpu_percent}%',
                        'details': {
                            'per_cpu_usage': per_cpu_percent,
                            'frequency': f'{cpu_freq.current:.1f} MHz' if cpu_freq else 'N/A',
                            'max_frequency': f'{cpu_freq.max:.1f} MHz' if cpu_freq else 'N/A',
                            'load_average': f'{load1:.2f} (1m), {load5:.2f} (5m), {load15:.2f} (15m)'
                        }
                })
            elif cpu_percent > 75:
                status = 'warning'
                alerts.append({
                    'component': 'CPU',
                    'status': 'warning',
                    'message': f'CPU usage high at {cpu_percent}%'
                })

            # Memory checks
            if memory.percent > 90:
                status = 'critical'
                alerts.append({
                    'component': 'Memory',
                    'status': 'critical',
                    'message': f'Memory usage critically high at {memory.percent}%',
                    'details': {
                        'total': f'{memory.total / (1024**3):.1f} GB',
                        'available': f'{memory.available / (1024**3):.1f} GB',
                        'used': f'{memory.used / (1024**3):.1f} GB',
                        'swap_used': f'{swap.used / (1024**3):.1f} GB',
                        'swap_free': f'{swap.free / (1024**3):.1f} GB'
                    }
                })
            elif memory.percent > 75:
                status = 'warning'
                alerts.append({
                    'component': 'Memory',
                    'status': 'warning',
                    'message': f'Memory usage high at {memory.percent}%'
                })

            # Disk checks
            if disk.percent > 90:
                status = 'critical'
                alerts.append({
                    'component': 'Disk',
                    'status': 'critical',
                    'message': f'Disk usage critically high at {disk.percent}%',
                    'details': {
                        'total': f'{disk.total / (1024**3):.1f} GB',
                        'used': f'{disk.used / (1024**3):.1f} GB',
                        'free': f'{disk.free / (1024**3):.1f} GB',
                        'read_bytes': f'{disk_io.read_bytes / (1024**2):.1f} MB',
                        'write_bytes': f'{disk_io.write_bytes / (1024**2):.1f} MB'
                    }
                })
            elif disk.percent > 75:
                status = 'warning'
                alerts.append({
                    'component': 'Disk',
                    'status': 'warning',
                    'message': f'Disk usage high at {disk.percent}%'
                })

            # Process checks
            if python_memory.rss / memory.total > 0.25:  # Python using >25% of memory
                alerts.append({
                    'component': 'Process',
                    'status': 'warning',
                    'message': 'Python process memory usage high',
                    'details': {
                        'memory_used': f'{python_memory.rss / (1024**2):.1f} MB',
                        'cpu_usage': f'{python_process.cpu_percent()}%',
                        'threads': python_process.num_threads(),
                        'total_processes': process_count
                    }
                })

            message = 'All systems operational' if not alerts else \
                     f'{len(alerts)} system alert(s) detected'

            return JsonResponse({
                'status': status,
                'message': message,
                'alerts': alerts,
                'metrics': {
                    'cpu': {
                        'usage_percent': cpu_percent,
                        'per_cpu_percent': per_cpu_percent,
                        'cores': cpu_count,
                        'frequency_mhz': round(cpu_freq.current, 1),
                        'ctx_switches': cpu_stats.ctx_switches,
                        'interrupts': cpu_stats.interrupts,
                        'load_average': {
                            '1min': round(load1, 2),
                            '5min': round(load5, 2),
                            '15min': round(load15, 2)
                        }
                    },
                    'memory': {
                        'total_gb': round(memory.total / (1024**3), 1),
                        'available_gb': round(memory.available / (1024**3), 1),
                        'used_gb': round(memory.used / (1024**3), 1),
                        'usage_percent': memory.percent,
                        'swap_used_gb': round(swap.used / (1024**3), 1),
                        'swap_free_gb': round(swap.free / (1024**3), 1)
                    },
                    'disk': {
                        'total_gb': round(disk.total / (1024**3), 1),
                        'used_gb': round(disk.used / (1024**3), 1),
                        'free_gb': round(disk.free / (1024**3), 1),
                        'usage_percent': disk.percent,
                        'io_counters': {
                            'read_mb': round(disk_io.read_bytes / (1024**2), 1),
                            'write_mb': round(disk_io.write_bytes / (1024**2), 1)
                        }
                    },
                    'process': {
                        'total_count': process_count,
                        'python_memory_mb': round(python_memory.rss / (1024**2), 1),
                        'python_threads': python_process.num_threads()
                    }
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f'Error checking system health: {str(e)}')
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to check system health',
                'error': str(e)
            }, status=500)

@method_decorator(require_POST, name='dispatch')
class ClearCacheView(SystemAdminRequiredMixin, View):
    """Clear system cache"""
    
    def post(self, request):
        try:
            cache.clear()
            logger.info(f'System cache cleared by {request.user.username}')
            return JsonResponse({
                'success': True,
                'message': 'Cache cleared successfully'
            })
        except Exception as e:
            logger.error(f'Cache clear failed: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Failed to clear cache: {str(e)}'
            }, status=500)

@method_decorator(require_POST, name='dispatch')
class RunDiagnosticsView(SystemAdminRequiredMixin, View):
    """Run system diagnostics"""
    
    def post(self, request):
        try:
            # Run various system checks
            checks = self.run_diagnostics()
            logger.info(f'System diagnostics run by {request.user.username}')
            return JsonResponse({
                'success': True,
                'message': 'Diagnostics completed successfully',
                'checks': checks
            })
        except Exception as e:
            logger.error(f'Diagnostics failed: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Diagnostics failed: {str(e)}'
            }, status=500)
    
    def run_diagnostics(self):
        """Run comprehensive system diagnostics"""
        checks = []
        
        try:
            # Check database connectivity
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks.append({
                    'name': 'Database Connection',
                    'status': 'success',
                    'message': 'Database connection is working'
                })
        except Exception as e:
            checks.append({
                'name': 'Database Connection',
                'status': 'danger',
                'message': f'Database error: {str(e)}'
            })

        # Add more diagnostic checks as needed
        return checks

class FinancialStatsAPIView(SystemAdminRequiredMixin, View):
    """API endpoint for financial statistics"""

    def get(self, request):
        try:
            # Get date range from request
            try:
                start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            except (TypeError, ValueError):
                start_date = (timezone.now() - timezone.timedelta(days=30)).date()
                
            try:
                end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
            except (TypeError, ValueError):
                end_date = timezone.now().date()
            
            # Get financial statistics
            stats = self.get_financial_statistics(start_date, end_date)
            
            return JsonResponse({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            logger.error(f'API Error: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class CartCountAPIView(LoginRequiredMixin, View):
    """API endpoint for cart count"""

    def get(self, request):
        try:
            from apps.ecommerce.models import ShoppingCart
            cart = ShoppingCart.objects.filter(user=request.user).first()
            count = cart.total_items if cart else 0
            return JsonResponse({'count': count})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Service Area Management Views
class ServiceAreaListView(LoginRequiredMixin, ListView):
    """List and manage service areas"""
    model = ServiceArea
    template_name = 'core/service_area_list.html'
    context_object_name = 'service_areas'
    paginate_by = 25

    def get_queryset(self):
        queryset = ServiceArea.objects.all()

        # Filter by area type
        area_type = self.request.GET.get('area_type')
        if area_type:
            queryset = queryset.filter(area_type=area_type)

        # Filter by coverage type
        coverage_type = self.request.GET.get('coverage_type')
        if coverage_type:
            queryset = queryset.filter(coverage_type=coverage_type)

        # Filter by county
        county = self.request.GET.get('county')
        if county:
            queryset = queryset.filter(county__icontains=county)

        # Filter by active status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(county__icontains=search_query) |
                Q(contact_person__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Order by county hierarchy
        return queryset.order_by('county', '-area_type', 'order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['area_types'] = ServiceArea.AREA_TYPES
        context['coverage_types'] = ServiceArea.COVERAGE_TYPES
        return context


class ServiceAreaDetailView(LoginRequiredMixin, DetailView):
    """View detailed service area information"""
    model = ServiceArea
    template_name = 'core/service_area_detail.html'
    context_object_name = 'service_area'


class ServiceAreaCreateView(LoginRequiredMixin, CreateView):
    """Create new service area"""
    model = ServiceArea
    template_name = 'core/service_area_form.html'
    fields = [
        'name', 'area_type', 'county', 'coverage_type', 'description',
        'contact_person', 'contact_phone', 'estimated_response_time',
        'latitude', 'longitude', 'center_point', 'boundary_geojson',
        'radius_km', 'is_active', 'order'
    ]

    def get_success_url(self):
        return reverse('core:service_area_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Auto-geocode if coordinates not provided
        if not form.cleaned_data.get('latitude') or not form.cleaned_data.get('longitude'):
            from .geographic_utils import get_geographic_service
            geo_service = get_geographic_service()

            location_string = f"{form.cleaned_data['name']}, Kenya"
            if form.cleaned_data.get('county') and form.cleaned_data['county'] != form.cleaned_data['name']:
                location_string = f"{form.cleaned_data['name']}, {form.cleaned_data['county']}, Kenya"

            geo_result = geo_service.geocode_location(location_string)
            if geo_result:
                form.instance.latitude = geo_result['latitude']
                form.instance.longitude = geo_result['longitude']
                messages.success(self.request, f'Auto-geocoded location: {form.instance.latitude}, {form.instance.longitude}')

        return super().form_valid(form)


class ServiceAreaUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing service area"""
    model = ServiceArea
    template_name = 'core/service_area_form.html'
    fields = [
        'name', 'area_type', 'county', 'coverage_type', 'description',
        'contact_person', 'contact_phone', 'estimated_response_time',
        'latitude', 'longitude', 'center_point', 'boundary_geojson',
        'radius_km', 'is_active', 'order'
    ]

    def get_success_url(self):
        return reverse('core:service_area_detail', kwargs={'pk': self.object.pk})


class ServiceAreaDeleteView(LoginRequiredMixin, DeleteView):
    """Delete service area"""
    model = ServiceArea
    template_name = 'core/service_area_confirm_delete.html'
    success_url = reverse_lazy('core:service_area_list')


class ServiceAreaBulkUpdateView(LoginRequiredMixin, View):
    """Bulk update service areas"""

    def post(self, request):
        action = request.POST.get('action')
        area_ids = request.POST.getlist('area_ids')

        if not area_ids:
            messages.error(request, 'No service areas selected.')
            return redirect('core:service_area_list')

        areas = ServiceArea.objects.filter(id__in=area_ids)

        if action == 'activate':
            areas.update(is_active=True)
            messages.success(request, f'Activated {areas.count()} service areas.')
        elif action == 'deactivate':
            areas.update(is_active=False)
            messages.success(request, f'Deactivated {areas.count()} service areas.')
        elif action == 'update_coordinates':
            updated_count = 0
            from .geographic_utils import get_geographic_service
            geo_service = get_geographic_service()

            for area in areas:
                location_string = f"{area.name}, Kenya"
                if area.county and area.county != area.name:
                    location_string = f"{area.name}, {area.county}, Kenya"

                geo_result = geo_service.geocode_location(location_string)
                if geo_result:
                    area.latitude = geo_result['latitude']
                    area.longitude = geo_result['longitude']
                    area.save(update_fields=['latitude', 'longitude'])
                    updated_count += 1

            messages.success(request, f'Updated coordinates for {updated_count} service areas.')
        elif action == 'clear_contacts':
            areas.update(contact_person='', contact_phone='', estimated_response_time='')
            messages.success(request, f'Cleared contact information for {areas.count()} service areas.')
        elif action == 'update_coverage_primary':
            areas.update(coverage_type='primary')
            messages.success(request, f'Updated {areas.count()} service areas to Primary coverage.')
        elif action == 'update_coverage_extended':
            areas.update(coverage_type='extended')
            messages.success(request, f'Updated {areas.count()} service areas to Extended coverage.')
        elif action == 'update_coverage_planned':
            areas.update(coverage_type='planned')
            messages.success(request, f'Updated {areas.count()} service areas to Planned coverage.')

        return redirect('core:service_area_list')


class CoverageCheckAPIView(View):
    """API endpoint for checking service area coverage"""

    def get(self, request):
        """Check if a location is covered by our services"""
        try:
            location = request.GET.get('location', '').strip()
            lat = request.GET.get('lat')
            lng = request.GET.get('lng')
            address = request.GET.get('address', '').strip()

            # Check if we have coordinates
            if lat and lng:
                try:
                    user_lat = float(lat)
                    user_lng = float(lng)
                    coordinates_provided = True
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid coordinates provided.',
                        'covered': False
                    }, status=400)
            else:
                coordinates_provided = False

            if not location and not coordinates_provided:
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a location or provide coordinates to check coverage.',
                    'covered': False
                })

            # Import ServiceArea here to avoid circular imports
            from .models import ServiceArea

            # Check coverage
            if coordinates_provided:
                result = self.check_coverage_by_coordinates(user_lat, user_lng, address or location)
            else:
                result = ServiceArea.check_coverage(location)

            # Log the coverage check for analytics
            try:
                from .models import ActivityLog
                log_message = f'Coverage check'
                if coordinates_provided:
                    log_message += f' by coordinates: {user_lat}, {user_lng}'
                else:
                    log_message += f' for location: {location}'

                ActivityLog.objects.create(
                    log_type='user',
                    severity='info',
                    message=log_message,
                    action='coverage_check',
                    description=f'Result: {result["message"]}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                # Don't fail the coverage check if logging fails
                logger.warning(f'Failed to log coverage check: {str(e)}')

            return JsonResponse({
                'success': True,
                'covered': result['covered'],
                'coverage_type': result['coverage_type'],
                'message': result['message'],
                'distance_km': result.get('distance_km'),
                'coordinates': {'lat': user_lat, 'lng': user_lng} if coordinates_provided else None,
                'area': {
                    'name': result['area'].name if result['area'] else None,
                    'coverage_type': result['area'].get_coverage_type_display() if result['area'] else None,
                    'description': result['area'].description if result['area'] else None,
                    'estimated_response_time': result['area'].estimated_response_time if result['area'] else None,
                    'contact_person': result['area'].contact_person if result['area'] else None,
                    'contact_phone': result['area'].contact_phone if result['area'] else None,
                } if result['area'] else None
            })

        except Exception as e:
            logger.error(f'Error checking coverage: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Sorry, we encountered an error while checking coverage. Please try again or contact us directly.',
                'covered': False
            }, status=500)

    def check_coverage_by_coordinates(self, latitude, longitude, address=""):
        """
        Check coverage using geographic coordinates.

        Args:
            latitude: User location latitude
            longitude: User location longitude
            address: Optional address string

        Returns:
            Coverage result dict
        """
        from .models import ServiceArea
        from .geographic_utils import get_geographic_service

        geo_service = get_geographic_service()

        # Check point-in-polygon for areas with boundaries
        all_active_areas = ServiceArea.objects.filter(is_active=True)

        for area in all_active_areas:
            # Check polygon boundaries first
            if area.boundary_geojson:
                try:
                    import json
                    boundary_data = json.loads(area.boundary_geojson) if isinstance(area.boundary_geojson, str) else area.boundary_geojson
                    if geo_service.is_point_in_polygon(latitude, longitude, boundary_data):
                        return {
                            'covered': True,
                            'coverage_type': area.coverage_type,
                            'area': area,
                            'distance_km': 0,
                            'message': f"Great! Your location is within our {area.get_coverage_type_display().lower()} area for {area.name}."
                        }
                except Exception:
                    pass  # Continue to next checks

            # Check circular boundaries
            if area.radius_km and area.latitude and area.longitude:
                if geo_service.is_point_in_circle(latitude, longitude, area.latitude, area.longitude, area.radius_km):
                    return {
                        'covered': True,
                        'coverage_type': area.coverage_type,
                        'area': area,
                        'distance_km': 0,
                        'message': f"Great! Your location is within our {area.get_coverage_type_display().lower()} area for {area.name}."
                    }

        # Find nearest service area
        nearest = geo_service.find_nearest_service_area(latitude, longitude, all_active_areas)
        if nearest:
            area = nearest['area']
            distance = nearest['distance_km']

            if distance <= 50:  # Within 50km, suggest extended coverage discussion
                return {
                    'covered': False,
                    'coverage_type': 'nearby',
                    'area': area,
                    'distance_km': distance,
                    'message': f"Your location is {distance:.1f}km from our nearest service area in {area.name}. We can discuss extended coverage options for your location."
                }
            else:
                return {
                    'covered': False,
                    'coverage_type': None,
                    'area': None,
                    'distance_km': distance,
                    'message': f"We're currently expanding our services. Your location is {distance:.1f}km from our nearest service area in {area.name}, but we'd love to discuss bringing solar solutions to your area."
                }

        # Fallback - no areas found
        return {
            'covered': False,
            'coverage_type': None,
            'area': None,
            'distance_km': None,
            'message': f"We're currently expanding our services. {address or 'Your location'} is not in our current service area, but we'd love to discuss bringing solar solutions to your area."
        }


# Newsletter Dashboard Views
class ManagementRequiredMixin(UserPassesTestMixin):
    """Verify that the current user has management privileges"""

    def test_func(self):
        return (self.request.user.is_authenticated and
                self.request.user.role in ['super_admin', 'director', 'manager', 'sales_manager'])

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to access this feature.')
            return redirect('accounts:login')
        else:
            messages.error(self.request, 'Access denied. Management privileges required.')
            return redirect('accounts:dashboard')


class NewsletterDashboardView(ManagementRequiredMixin, TemplateView):
    """Main newsletter dashboard with statistics and overview"""
    template_name = 'dashboard/newsletter_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from .models import NewsletterSubscriber, NewsletterCampaign, NewsletterSendLog
        from django.db.models import Count, Q, Sum
        import datetime

        # Get date ranges
        now = timezone.now()
        last_30_days = now - datetime.timedelta(days=30)
        last_7_days = now - datetime.timedelta(days=7)

        # Subscriber statistics
        total_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
        new_subscribers_30d = NewsletterSubscriber.objects.filter(
            subscribed_at__gte=last_30_days,
            is_active=True
        ).count()
        new_subscribers_7d = NewsletterSubscriber.objects.filter(
            subscribed_at__gte=last_7_days,
            is_active=True
        ).count()

        # Campaign statistics
        total_campaigns = NewsletterCampaign.objects.count()
        sent_campaigns = NewsletterCampaign.objects.filter(status='sent').count()
        draft_campaigns = NewsletterCampaign.objects.filter(status='draft').count()

        # Recent campaigns with analytics
        recent_campaigns = NewsletterCampaign.objects.select_related('created_by').order_by('-created_at')[:5]

        # Calculate overall analytics
        total_sent = NewsletterSendLog.objects.count()
        total_opens = NewsletterSendLog.objects.filter(opened_at__isnull=False).count()
        total_clicks = NewsletterSendLog.objects.filter(clicked_at__isnull=False).count()

        overall_open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
        overall_click_rate = (total_clicks / total_sent * 100) if total_sent > 0 else 0

        # Recent subscriber activity
        recent_subscribers = NewsletterSubscriber.objects.filter(
            is_active=True
        ).order_by('-subscribed_at')[:10]

        context.update({
            'total_subscribers': total_subscribers,
            'new_subscribers_30d': new_subscribers_30d,
            'new_subscribers_7d': new_subscribers_7d,
            'total_campaigns': total_campaigns,
            'sent_campaigns': sent_campaigns,
            'draft_campaigns': draft_campaigns,
            'recent_campaigns': recent_campaigns,
            'total_sent': total_sent,
            'total_opens': total_opens,
            'total_clicks': total_clicks,
            'overall_open_rate': round(overall_open_rate, 1),
            'overall_click_rate': round(overall_click_rate, 1),
            'recent_subscribers': recent_subscribers,
        })

        return context


class NewsletterCampaignListView(ManagementRequiredMixin, ListView):
    """List all newsletter campaigns"""
    model = NewsletterCampaign
    template_name = 'dashboard/newsletter_campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

    def get_queryset(self):
        queryset = NewsletterCampaign.objects.select_related('created_by').order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(subject__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = NewsletterCampaign.STATUS_CHOICES
        return context


class NewsletterCampaignCreateView(ManagementRequiredMixin, CreateView):
    """Create new newsletter campaign"""
    model = NewsletterCampaign
    template_name = 'dashboard/newsletter_campaign_form.html'
    fields = ['title', 'subject', 'preview_text', 'content', 'template_type', 'call_to_action_text', 'call_to_action_url', 'status']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set default status to draft for new campaigns
        form.fields['status'].initial = 'draft'
        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Campaign "{form.instance.title}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:newsletter_campaign_detail', kwargs={'pk': self.object.pk})


class NewsletterCampaignUpdateView(ManagementRequiredMixin, UpdateView):
    """Edit newsletter campaign"""
    model = NewsletterCampaign
    template_name = 'dashboard/newsletter_campaign_form.html'
    fields = ['title', 'subject', 'preview_text', 'content', 'template_type', 'call_to_action_text', 'call_to_action_url', 'status']

    def form_valid(self, form):
        messages.success(self.request, f'Campaign "{form.instance.title}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:newsletter_campaign_detail', kwargs={'pk': self.object.pk})


class NewsletterCampaignDetailView(ManagementRequiredMixin, DetailView):
    """View campaign details and analytics"""
    model = NewsletterCampaign
    template_name = 'dashboard/newsletter_campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.object

        # Get send logs with analytics
        send_logs = campaign.send_logs.all()
        total_sent = send_logs.count()
        total_opens = send_logs.filter(opened_at__isnull=False).count()
        total_clicks = send_logs.filter(clicked_at__isnull=False).count()
        total_bounces = send_logs.filter(delivery_status='bounced').count()
        total_failed = send_logs.filter(delivery_status='failed').count()

        # Calculate rates
        open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicks / total_sent * 100) if total_sent > 0 else 0
        delivery_rate = ((total_sent - total_failed - total_bounces) / total_sent * 100) if total_sent > 0 else 0

        context.update({
            'send_logs': send_logs.order_by('-sent_at')[:50],  # Show recent 50
            'total_sent': total_sent,
            'total_opens': total_opens,
            'total_clicks': total_clicks,
            'total_bounces': total_bounces,
            'total_failed': total_failed,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1),
            'delivery_rate': round(delivery_rate, 1),
        })

        return context


class NewsletterCampaignSendView(ManagementRequiredMixin, View):
    """Send a newsletter campaign"""

    def post(self, request, pk):
        try:
            campaign = NewsletterCampaign.objects.get(pk=pk)

            if not campaign.can_send():
                messages.error(request, f'Campaign "{campaign.title}" cannot be sent (status: {campaign.get_status_display()})')
                return redirect('core:newsletter_campaign_detail', pk=pk)

            # Use the newsletter service to send
            from .newsletter_service import NewsletterService
            service = NewsletterService()
            result = service.send_campaign(campaign, request.user)

            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, result['error'])

        except NewsletterCampaign.DoesNotExist:
            messages.error(request, 'Campaign not found.')
        except Exception as e:
            messages.error(request, f'Error sending campaign: {str(e)}')

        return redirect('core:newsletter_campaign_detail', pk=pk)


class NewsletterSubscriberListView(ManagementRequiredMixin, ListView):
    """Manage newsletter subscribers"""
    model = NewsletterSubscriber
    template_name = 'dashboard/newsletter_subscriber_list.html'
    context_object_name = 'subscribers'
    paginate_by = 25

    def get_queryset(self):
        queryset = NewsletterSubscriber.objects.all().order_by('-subscribed_at')

        # Filter by active status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics
        total_subscribers = NewsletterSubscriber.objects.count()
        active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()

        context.update({
            'total_subscribers': total_subscribers,
            'active_subscribers': active_subscribers,
            'inactive_subscribers': total_subscribers - active_subscribers,
        })

        return context


class NewsletterSubscriberDetailView(ManagementRequiredMixin, DetailView):
    """View subscriber details and activity"""
    model = NewsletterSubscriber
    template_name = 'dashboard/newsletter_subscriber_detail.html'
    context_object_name = 'subscriber'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscriber = self.object

        # Get subscriber's send logs
        send_logs = subscriber.send_logs.select_related('campaign').order_by('-sent_at')[:20]

        # Calculate email statistics
        total_sent = subscriber.send_logs.count()
        total_opens = subscriber.send_logs.filter(opened_at__isnull=False).count()
        total_clicks = subscriber.send_logs.filter(clicked_at__isnull=False).count()

        # Calculate rates for template display
        open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicks / total_sent * 100) if total_sent > 0 else 0

        context.update({
            'send_logs': send_logs,
            'total_sent': total_sent,
            'total_opens': total_opens,
            'total_clicks': total_clicks,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1),
        })
        return context


class NewsletterSubscriberToggleView(ManagementRequiredMixin, View):
    """Toggle subscriber active status"""

    def post(self, request, pk):
        try:
            subscriber = NewsletterSubscriber.objects.get(pk=pk)
            subscriber.is_active = not subscriber.is_active

            if not subscriber.is_active:
                subscriber.unsubscribed_at = timezone.now()
            else:
                subscriber.unsubscribed_at = None

            subscriber.save()

            status = 'activated' if subscriber.is_active else 'deactivated'
            messages.success(request, f'Subscriber {subscriber.email} has been {status}.')

        except NewsletterSubscriber.DoesNotExist:
            messages.error(request, 'Subscriber not found.')
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')

        return redirect('core:newsletter_subscriber_detail', pk=pk)


# Newsletter Tracking Views
class TrackEmailOpenView(View):
    """Track email opens via pixel tracking"""

    def get(self, request, log_id):
        """Serve tracking pixel and record open event"""
        try:
            from .newsletter_service import NewsletterService
            service = NewsletterService()

            success = service.track_email_open(log_id)

            # Return 1x1 transparent pixel
            response = HttpResponse(content_type='image/png')
            # Create a 1x1 transparent PNG pixel
            pixel_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            response.write(pixel_data)

            return response

        except Exception as e:
            logger.error(f'Email tracking error: {str(e)}')
            # Still return pixel even on error to avoid broken images
            response = HttpResponse(content_type='image/png')
            pixel_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            response.write(pixel_data)
            return response


class TrackEmailClickView(View):
    """Track email clicks and redirect to target URL"""

    def get(self, request, log_id):
        """Track click and redirect to target URL"""
        try:
            from .newsletter_service import NewsletterService
            service = NewsletterService()

            redirect_url = request.GET.get('url', '')
            target_url = service.track_email_click(log_id, redirect_url)

            if target_url:
                return redirect(target_url)
            else:
                # Default fallback if no target URL
                return redirect('core:home')

        except Exception as e:
            logger.error(f'Email click tracking error: {str(e)}')
            return redirect('core:home')


class UnsubscribeView(View):
    """Handle newsletter unsubscribe requests"""

    def get(self, request, token, subscriber_id):
        """Show unsubscribe confirmation page"""
        try:
            from .newsletter_service import NewsletterService
            service = NewsletterService()

            # Verify token and get subscriber
            result = service.process_unsubscribe(subscriber_id, token)

            if result['success']:
                context = {
                    'subscriber': result['subscriber'],
                    'success': True,
                    'message': result['message']
                }
            else:
                context = {
                    'success': False,
                    'error': result['error']
                }

            return render(request, 'core/newsletter_unsubscribe.html', context)

        except Exception as e:
            logger.error(f'Unsubscribe error: {str(e)}')
            return render(request, 'core/newsletter_unsubscribe.html', {
                'success': False,
                'error': 'An error occurred while processing your unsubscribe request.'
            })
