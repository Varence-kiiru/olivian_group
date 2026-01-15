from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import views as auth_views
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.db import models
from apps.core.email_utils import EmailService
from .models import User
from django.http import HttpResponse
from django import forms
from decimal import Decimal

# Import chat models for chat management functionality
from apps.chat.models import ChatRoom, Message, MessageReadStatus, UserActivity, MessageReaction, NotificationPreference
from apps.chat.admin import has_chat_admin_permission

class RegisterView(CreateView):
    model = User
    template_name = 'accounts/register.html'
    # Update fields to match template
    fields = [
        'first_name',
        'last_name',
        'email',
        'phone',
        'username',
        'password',
        'customer_type',  # For account type
        'company_name'    # Optional for business customers
    ]
    success_url = reverse_lazy('accounts:registration_pending')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Add CSS classes and set specific IDs
        form.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_password'
        })

        form.fields['password2'] = forms.CharField(
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'id': 'id_password2'
            }),
            label='Confirm Password',
            required=True
        )

        form.fields['customer_type'].widget = forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_customer_type'
        })

        # Add classes to other fields
        for field_name, field in form.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        # Change password field to PasswordInput widget
        form.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control'})

        # Add confirm password field
        form.fields['password2'] = forms.CharField(
            widget=forms.PasswordInput(attrs={'class': 'form-control'}),
            label='Confirm Password',
            required=True
        )

        # Customize account type choices
        form.fields['customer_type'].widget = forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_account_type'
        })
        form.fields['customer_type'].choices = [
            ('', 'Select Account Type'),
            ('individual', 'Customer - Individual'),
            ('business', 'Customer - Business'),
            ('government', 'Customer - Government')
        ]

        return form

    def form_valid(self, form):
        # Check if passwords match
        if form.cleaned_data['password'] != form.cleaned_data['password2']:
            form.add_error('password2', 'Passwords do not match')
            return self.form_invalid(form)

        # Create the user object but don't save yet
        user = form.save(commit=False)

        # Set the password properly
        user.set_password(form.cleaned_data['password'])

        # Set default role and status
        user.role = 'customer'
        user.is_active = False  # Will be activated after email verification

        # Save the user
        user.save()

        # Generate verification token and send email
        token = user.generate_verification_token()
        verification_url = self.request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': str(token)})
        )

        # Send verification email
        try:
            EmailService.send_email_verification(user, verification_url)
            messages.success(
                self.request,
                'Account created! Please check your email to verify your account.'
            )
        except Exception as e:
            messages.warning(
                self.request,
                'Account created but verification email failed to send. Please contact support.'
            )
            
        return super().form_valid(form)

class CustomLoginView(auth_views.LoginView):
    """Custom login view with checkpoint system for user type detection"""

    def get_template_names(self):
        """Return appropriate template based on request context"""
        # Check if explicitly requesting staff portal
        if self.request.GET.get('staff') == '1':
            return ['accounts/login_staff.html']

        # Default to customer login
        return ['accounts/login_customer.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.core.models import CompanySettings
        
        # Get company settings
        try:
            company = CompanySettings.objects.first()
            context['company'] = company
            
            # Add specific logo paths
            if company:
                context.update({
                    'company_logo': company.logo.url if company.logo else None,
                    'company_favicon': company.favicon.url if company.favicon else None
                })
        except Exception as e:
            print(f"Error loading company settings: {e}")

        return context

    def form_valid(self, form):
        user = form.get_user()

        # Validate user type matches the portal they're trying to access
        is_staff_portal = self.request.GET.get('staff') == '1'
        staff_roles = ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person',
                      'project_manager', 'inventory_manager', 'cashier', 'technician']

        # If staff trying to log in through customer portal, redirect to staff portal
        if not is_staff_portal and user.role in staff_roles:
            messages.warning(
                self.request,
                'Please use the staff portal to access your account.'
            )
            return redirect(reverse('accounts:login') + '?staff=1')

        # If customer trying to log in through staff portal, redirect to customer portal
        if is_staff_portal and user.role == 'customer':
            messages.error(
                self.request,
                'This account is not authorized for staff portal access. Please use the customer portal.'
            )
            return redirect('accounts:login')

        # Check if email is verified (for customers)
        if user.role == 'customer' and not user.email_verified:
            messages.error(
                self.request,
                'Please verify your email address before logging in. Check your inbox for a verification link.'
            )
            return redirect('accounts:registration_pending')

        # Check if user needs to change password (new staff with temp password)
        if user.role in staff_roles and not user.password_changed:
            messages.info(
                self.request,
                'Welcome! Please change your temporary password to continue.'
            )
            # Log the user in first, then redirect to password change
            from django.contrib.auth import login
            login(self.request, user)
            return redirect('accounts:change_password')

        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_template_names(self):
        role_templates = {
            'customer': 'accounts/customer_dashboard.html',
            'sales_person': 'accounts/sales_dashboard.html',
            'sales_manager': 'accounts/sales_dashboard.html',
            'manager': 'accounts/manager_dashboard.html',
            'super_admin': 'accounts/admin_dashboard.html',
            'director': 'accounts/director_dashboard.html',
            'project_manager': 'accounts/manager_dashboard.html',
            'inventory_manager': 'accounts/manager_dashboard.html',
            'cashier': 'accounts/sales_dashboard.html',
            'technician': 'accounts/sales_dashboard.html',
        }
        return [role_templates.get(self.request.user.role, 'accounts/dashboard.html')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from apps.quotations.models import Quotation, Customer
        from apps.projects.models import Project
        from apps.ecommerce.models import Order
        from apps.products.models import Product
        from apps.inventory.models import InventoryItem
        from apps.budget.models import Budget, ExpenseRequest
        from django.db.models import Q, Sum, Count, Avg, F
        from django.utils import timezone
        from datetime import datetime, timedelta
        import calendar

        # Add debugging info for production issues
        context['user_role'] = self.request.user.role
        context['debug_info'] = {
            'is_authenticated': self.request.user.is_authenticated,
            'username': self.request.user.username,
            'role': self.request.user.role,
            'is_staff': self.request.user.is_staff,
            'template_used': self.get_template_names()[0]
        }

        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # ADMIN DASHBOARD DATA
        if self.request.user.role == 'super_admin':
            try:
                # Admin Stats
                total_users = User.objects.count()
                new_users_this_month = User.objects.filter(date_joined__gte=current_month_start).count()
                
                # Revenue calculations
                current_month_revenue = Order.objects.filter(
                    created_at__gte=current_month_start,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                last_month_revenue = Order.objects.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                revenue_change = ((current_month_revenue - last_month_revenue) / max(last_month_revenue, 1)) * 100 if last_month_revenue > 0 else 0
                
                # Order calculations
                current_month_orders = Order.objects.filter(created_at__gte=current_month_start).count()
                last_month_orders = Order.objects.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end
                ).count()
                orders_change = ((current_month_orders - last_month_orders) / max(last_month_orders, 1)) * 100 if last_month_orders > 0 else 0
                
                # Projects
                active_projects = Project.objects.filter(status__in=['planning', 'in_progress', 'scheduled']).count()
                completed_projects = Project.objects.filter(status='completed').count()
                
                # Inventory
                inventory_items = Product.objects.filter(status='active').count()
                try:
                    low_stock_items = InventoryItem.objects.filter(
                        quantity_on_hand__lte=F('reorder_point')
                    ).count()
                except:
                    low_stock_items = 0
                
                context['admin_stats'] = {
                    'total_users': total_users,
                    'new_users_this_month': new_users_this_month,
                    'total_revenue': current_month_revenue,
                    'revenue_change': round(revenue_change, 1),
                    'total_orders': current_month_orders,
                    'orders_change': round(orders_change, 1),
                    'active_projects': active_projects,
                    'completed_projects': completed_projects,
                    'inventory_items': inventory_items,
                    'low_stock_items': low_stock_items,
                    'system_uptime': 99.9,
                }
                
                # User statistics by role
                context['user_stats'] = {
                    'admin_count': User.objects.filter(role='super_admin').count(),
                    'manager_count': User.objects.filter(role__in=['manager', 'project_manager', 'inventory_manager']).count(),
                    'sales_count': User.objects.filter(role__in=['sales_manager', 'sales_person']).count(),
                    'customer_count': User.objects.filter(role='customer').count(),
                }
                
                # Recent users
                context['recent_users'] = User.objects.exclude(role='customer').order_by('-date_joined')[:10]
                
                # Financial data
                total_revenue_all_time = Order.objects.filter(
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                context['financial_data'] = {
                    'total_revenue': total_revenue_all_time,
                    'monthly_revenue': current_month_revenue,
                    'total_expenses': 0,  # You can add expense tracking later
                    'net_profit': current_month_revenue,  # Simplified for now
                    'pending_payments': Order.objects.filter(status='pending_payment').aggregate(total=Sum('total_amount'))['total'] or 0,
                    'outstanding_invoices': Quotation.objects.filter(status='approved').aggregate(total=Sum('total_amount'))['total'] or 0,
                }
                
                # Chart data for admin dashboard
                monthly_data = []
                for i in range(6):
                    month_start = (now - timedelta(days=i*30)).replace(day=1)
                    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
                    month_revenue = Order.objects.filter(
                        created_at__gte=month_start,
                        created_at__lte=month_end,
                        status__in=['completed', 'delivered', 'paid']
                    ).aggregate(total=Sum('total_amount'))['total'] or 0
                    monthly_data.append(month_revenue)
                
                context['chart_data'] = {
                    'revenue_percentage': 30,
                    'orders_percentage': 25,
                    'users_percentage': 20,
                    'projects_percentage': 15,
                    'inventory_percentage': 10,
                }
                
                # System health with real backup timestamp
                from apps.core.views import SystemMaintenanceView
                last_backup = SystemMaintenanceView().get_last_backup_date()
                backup_status = 'good' if last_backup else 'warning'
                last_backup_display = 'Never' if not last_backup else (
                    'Just now' if (timezone.now() - last_backup).total_seconds() < 3600 else
                    last_backup.strftime('%Y-%m-%d %H:%M:%S')
                ) if last_backup else 'Never'

                context['system_health'] = {
                    'database_status': 'excellent',
                    'database_performance': 'Excellent',
                    'response_status': 'excellent',
                    'response_time': 'Fast',
                    'storage_status': 'good',
                    'storage_usage': 45,
                    'memory_status': 'warning',
                    'memory_usage': 68,
                    'api_status': 'excellent',
                    'api_performance': 'Operational',
                    'backup_status': backup_status,
                    'last_backup': last_backup_display,
                }
                
            except Exception as e:
                print(f"Admin dashboard error: {e}")
                context['admin_stats'] = {
                    'total_users': 0, 'new_users_this_month': 0, 'total_revenue': 0,
                    'revenue_change': 0, 'total_orders': 0, 'orders_change': 0,
                    'active_projects': 0, 'completed_projects': 0, 'inventory_items': 0,
                    'low_stock_items': 0, 'system_uptime': 99.9,
                }
        
        # MANAGER DASHBOARD DATA
        elif self.request.user.role in ['manager', 'project_manager', 'inventory_manager']:
            try:
                # Manager Stats
                current_revenue = Order.objects.filter(
                    created_at__gte=current_month_start,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                last_revenue = Order.objects.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                revenue_change = ((current_revenue - last_revenue) / max(last_revenue, 1)) * 100 if last_revenue > 0 else 0
                net_profit = current_revenue * Decimal('0.2')  # Assuming 20% margin
                profit_change = revenue_change  # Simplified
                
                active_projects = Project.objects.filter(status__in=['planning', 'in_progress', 'scheduled']).count()
                current_projects = Project.objects.filter(created_at__gte=current_month_start).count()
                last_projects = Project.objects.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end
                ).count()
                projects_change = current_projects - last_projects
                
                # Team performance (simplified)
                team_performance = min(85, (current_revenue / max(1000000, 1)) * 100)  # Against 1M target
                
                context['manager_stats'] = {
                    'total_revenue': current_revenue,
                    'revenue_change': round(revenue_change, 1),
                    'net_profit': net_profit,
                    'profit_change': round(profit_change, 1),
                    'active_projects': active_projects,
                    'projects_change': projects_change,
                    'team_performance': round(team_performance, 1),
                    'performance_change': 5,  # Placeholder
                    'budget_utilization': 65,  # Placeholder
                    'budget_remaining': 500000,  # Placeholder
                }
                
                # Team members
                staff_roles = ['manager', 'sales_manager', 'sales_person', 'project_manager', 
                              'inventory_manager', 'cashier', 'technician']
                context['team_members'] = User.objects.filter(
                    role__in=staff_roles,
                    is_active_employee=True
                ).exclude(pk=self.request.user.pk)[:10]
                
                # Budget categories (if budget module exists)
                context['budget_categories'] = []  # Placeholder
                
                # Chart data
                context['chart_data'] = {
                    'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    'revenue': [0, 0, 0, 0, 0, current_revenue],
                    'profit': [0, 0, 0, 0, 0, net_profit],
                }
                
                # Resource allocation
                context['resource_allocation'] = {
                    'sales_utilization': 75,
                    'projects_utilization': 85,
                    'inventory_utilization': 60,
                }
                
                # Pending approvals (if budget/expense requests exist)
                context['pending_approvals'] = ExpenseRequest.objects.filter(
                    status='pending'
                ) if hasattr(ExpenseRequest, 'objects') else []
                
            except Exception as e:
                print(f"Manager dashboard error: {e}")
                context['manager_stats'] = {
                    'total_revenue': 0, 'revenue_change': 0, 'net_profit': 0,
                    'profit_change': 0, 'active_projects': 0, 'projects_change': 0,
                    'team_performance': 0, 'performance_change': 0,
                    'budget_utilization': 0, 'budget_remaining': 0,
                }
                context['team_members'] = []
        
        # DIRECTOR DASHBOARD DATA
        elif self.request.user.role == 'director':
            try:
                # Director Overview - Comprehensive company metrics from real data
                current_revenue = Order.objects.filter(
                    created_at__gte=current_month_start,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

                last_revenue = Order.objects.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

                revenue_change = ((current_revenue - last_revenue) / max(last_revenue, Decimal('1'))) * 100 if last_revenue > 0 else Decimal('0')
                net_profit = current_revenue * Decimal('0.25')  # Assuming 25% margin
                profit_change = revenue_change

                # Company-wide metrics
                active_projects = Project.objects.filter(status__in=['planning', 'in_progress', 'scheduled']).count()
                completed_projects = Project.objects.filter(status='completed').count()
                total_customers = User.objects.filter(role='customer').count()

                # Department performance metrics
                total_staff = User.objects.exclude(role='customer').count()
                sales_team = User.objects.filter(role__in=['sales_manager', 'sales_person']).count()
                technical_team = User.objects.filter(role__in=['project_manager', 'technician']).count()
                management_team = User.objects.filter(role__in=['manager', 'inventory_manager', 'director']).count()

                # Year-over-year growth calculations
                current_year_revenue = Order.objects.filter(
                    created_at__gte=now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

                last_year_revenue = Order.objects.filter(
                    created_at__gte=(now - timedelta(days=365)).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                    created_at__lte=now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1),
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

                yoy_growth = ((current_year_revenue - last_year_revenue) / max(last_year_revenue, Decimal('1'))) * 100 if last_year_revenue > 0 else Decimal('0')

                context['director_stats'] = {
                    'total_revenue': current_revenue,
                    'revenue_change': round(float(revenue_change), 1),
                    'net_profit': net_profit,
                    'profit_change': round(float(profit_change), 1),
                    'yoy_growth': round(float(yoy_growth), 1),
                    'active_projects': active_projects,
                    'completed_projects': completed_projects,
                    'total_customers': total_customers,
                    'total_staff': total_staff,
                    'sales_team': sales_team,
                    'technical_team': technical_team,
                    'management_team': management_team,
                    'company_health': min(95, float((current_revenue / max(Decimal('2000000'), Decimal('1'))) * 100)),  # Against 2M target
                    'budget_utilization': 75,  # Keep placeholder for now
                    'strategic_initiatives': active_projects,  # Number of active projects
                }

                # Real Key Performance Indicators calculation
                # Revenue KPI against monthly target (500K)
                revenue_target = Decimal('500000')
                revenue_kpi = min(100, float((current_revenue / revenue_target) * 100))

                # Customer satisfaction from completed projects feedback (placeholder until feedback system added)
                customer_satisfaction = 85  # Will be updated with real feedback data

                # Employee engagement (placeholder - requires survey system)
                employee_engagement = 88  # Will be updated with real survey data

                # Operational efficiency from project completion rates
                completed_projects_query = Project.objects.filter(status='completed')
                if completed_projects_query.exists():
                    avg_completion_rate = completed_projects_query.aggregate(
                        avg_rate=Avg('completion_percentage')
                    )['avg_rate'] or 0
                    operational_efficiency = min(100, float(avg_completion_rate))
                else:
                    operational_efficiency = 75

                context['kpis'] = {
                    'revenue_kpi': round(revenue_kpi, 1),
                    'customer_satisfaction': customer_satisfaction,
                    'employee_engagement': employee_engagement,
                    'operational_efficiency': round(operational_efficiency, 1),
                }

                # Department performance from real data
                context['department_performance'] = []

                # Sales & Marketing performance
                monthly_orders = Order.objects.filter(created_at__gte=current_month_start).count()
                sales_performance = min(100, (monthly_orders / max(50, 1)) * 100)  # Target: 50 orders/month
                context['department_performance'].append({
                    'name': 'Sales & Marketing',
                    'headcount': sales_team,
                    'performance': round(sales_performance, 1),
                    'budget_allocation': '25%',
                    'key_metric': f'{monthly_orders} orders this month'
                })

                # Technical Operations performance
                projects_this_month = Project.objects.filter(created_at__gte=current_month_start).count()
                tech_performance = min(100, (active_projects / max(20, 1)) * 100)  # Target: 20 active projects
                context['department_performance'].append({
                    'name': 'Technical Operations',
                    'headcount': technical_team,
                    'performance': round(tech_performance, 1),
                    'budget_allocation': '35%',
                    'key_metric': f'{active_projects} active projects'
                })

                # Management performance
                management_performance = min(100, (total_staff / max(15, 1)) * 100)  # Growth target
                context['department_performance'].append({
                    'name': 'Management',
                    'headcount': management_team,
                    'performance': round(management_performance, 1),
                    'budget_allocation': '20%',
                    'key_metric': f'{total_staff} total team members'
                })

                # Strategic initiatives from active high-value projects
                strategic_projects = Project.objects.filter(
                    status__in=['planning', 'in_progress', 'scheduled']
                ).order_by('-contract_value')[:3]

                context['strategic_initiatives'] = []
                for project in strategic_projects:
                    # Calculate progress from completed tasks
                    total_tasks = project.tasks.count()
                    completed_tasks = project.tasks.filter(status='completed').count()
                    progress = int((completed_tasks / max(total_tasks, 1)) * 100)

                    context['strategic_initiatives'].append({
                        'name': project.name[:30] + '...' if len(project.name) > 30 else project.name,
                        'progress': progress,
                        'due_date': project.target_completion.strftime('%b %Y') if project.target_completion else 'TBD'
                    })

                # Executive alerts from real system data
                context['executive_alerts'] = []

                # Projects behind schedule
                overdue_projects = Project.objects.filter(
                    target_completion__lt=timezone.now().date(),
                    status__in=['planning', 'in_progress', 'scheduled']
                ).count()
                if overdue_projects > 0:
                    context['executive_alerts'].append({
                        'type': 'warning',
                        'message': f'{overdue_projects} project(s) behind schedule'
                    })

                # Low stock alerts (if inventory system exists)
                try:
                    from apps.inventory.models import InventoryItem
                    low_stock_items = InventoryItem.objects.filter(
                        quantity_on_hand__lte=models.F('reorder_point')
                    ).count()
                    if low_stock_items > 0:
                        context['executive_alerts'].append({
                            'type': 'warning',
                            'message': f'{low_stock_items} items at low stock levels'
                        })
                except (ImportError, AttributeError):
                    pass  # Inventory system not fully implemented

                # Revenue target achievement
                if revenue_kpi >= 90:
                    context['executive_alerts'].append({
                        'type': 'success',
                        'message': f'Monthly revenue target {revenue_kpi:.1f}% achieved'
                    })
                elif revenue_kpi >= 75:
                    context['executive_alerts'].append({
                        'type': 'info',
                        'message': f'Revenue at {revenue_kpi:.1f}% of monthly target'
                    })

                # Budget approaching limits (if budget system available)
                try:
                    from apps.budget.models import Budget
                    budget_alerts = Budget.objects.filter(
                        spent_amount__gte=models.F('total_amount') * 0.85
                    ).count()
                    if budget_alerts > 0:
                        context['executive_alerts'].append({
                            'type': 'warning',
                            'message': f'{budget_alerts} budget(s) approaching 85% utilization'
                        })
                except (ImportError, AttributeError):
                    pass

                # Add success message if no alerts
                if not context['executive_alerts']:
                    context['executive_alerts'].append({
                        'type': 'success',
                        'message': 'All systems operating within normal parameters'
                    })

                # Real chart data - Monthly revenue and profit trends for last 9 months
                monthly_data = []
                labels = []
                revenue_data = []
                profit_data = []
                customers_data = []

                for i in range(8, -1, -1):  # Last 9 months
                    month_start = (now - timedelta(days=i*30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
                    month_label = month_start.strftime('%b')

                    # Revenue for this month
                    month_revenue = Order.objects.filter(
                        created_at__gte=month_start,
                        created_at__lte=month_end,
                        status__in=['completed', 'delivered', 'paid']
                    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

                    # Customers acquired this month
                    month_customers = User.objects.filter(
                        date_joined__gte=month_start,
                        date_joined__lte=month_end,
                        role='customer'
                    ).count()

                    labels.append(month_label)
                    revenue_data.append(float(month_revenue))
                    profit_data.append(float(month_revenue * Decimal('0.25')))  # 25% profit margin
                    customers_data.append(month_customers)

                context['chart_data'] = {
                    'labels': labels,
                    'revenue': revenue_data,
                    'profit': profit_data,
                    'customers': customers_data,
                }

                # Resource allocation from real project assignments
                context['resource_allocation'] = {}

                # Sales team utilization
                sales_assigned_tasks = 0
                sales_team_members = User.objects.filter(role__in=['sales_manager', 'sales_person'])
                if sales_team_members.exists():
                    # Count active leads/opportunities assigned to sales team
                    from apps.crm.models import Lead, Opportunity
                    sales_assigned_tasks = Lead.objects.filter(
                        assigned_to__in=sales_team_members,
                        status__in=['new', 'contacted', 'qualified']
                    ).count() + Opportunity.objects.filter(
                        assigned_to__in=sales_team_members,
                        stage__in=['qualification', 'needs_analysis', 'proposal', 'negotiation']
                    ).count()
                    sales_capacity = sales_team_members.count() * 10  # Assume 10 active deals per salesperson
                    sales_utilization = min(100, (sales_assigned_tasks / max(sales_capacity, 1)) * 100)
                else:
                    sales_utilization = 0
                context['resource_allocation']['sales_utilization'] = round(sales_utilization, 1)

                # Project team utilization
                project_team_members = User.objects.filter(role__in=['project_manager', 'technician'])
                project_utilization = min(100, (active_projects / max(project_team_members.count() * 3, 1)) * 100)  # Assume 3 projects per team member
                context['resource_allocation']['projects_utilization'] = round(project_utilization, 1)

                # Inventory utilization (placeholder)
                context['resource_allocation']['inventory_utilization'] = 78

                # HR utilization
                hr_utilization = min(100, (total_staff / max(25, 1)) * 100)  # HR capacity based on team size
                context['resource_allocation']['hr_utilization'] = round(hr_utilization, 1)

                # Financial utilization
                financial_utilization = 95  # Assume finance team at capacity
                context['resource_allocation']['financial_utilization'] = financial_utilization

            except Exception as e:
                print(f"Director dashboard error: {e}")
                context['director_stats'] = {
                    'total_revenue': 0, 'revenue_change': 0, 'net_profit': 0,
                    'profit_change': 0, 'yoy_growth': 0, 'active_projects': 0,
                    'completed_projects': 0, 'total_customers': 0, 'total_staff': 0,
                    'sales_team': 0, 'technical_team': 0, 'management_team': 0,
                }
                context['department_performance'] = []
                context['strategic_initiatives'] = []
                context['executive_alerts'] = []

        # SALES DASHBOARD DATA
        elif self.request.user.role in ['sales_person', 'sales_manager', 'cashier', 'technician']:
            try:
                # Sales person stats
                user_quotations = Quotation.objects.filter(created_by=self.request.user)
                user_orders = Order.objects.filter(created_by=self.request.user) if hasattr(Order, 'created_by') else Order.objects.all()
                
                current_revenue = user_orders.filter(
                    created_at__gte=current_month_start,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                last_revenue = user_orders.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                revenue_change = ((current_revenue - last_revenue) / max(last_revenue, 1)) * 100 if last_revenue > 0 else 0
                
                current_orders = user_orders.filter(created_at__gte=current_month_start).count()
                last_orders = user_orders.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end
                ).count()
                orders_change = ((current_orders - last_orders) / max(last_orders, 1)) * 100 if last_orders > 0 else 0
                
                current_quotations = user_quotations.filter(created_at__gte=current_month_start).count()
                last_quotations = user_quotations.filter(
                    created_at__gte=last_month_start,
                    created_at__lte=last_month_end
                ).count()
                quotations_change = ((current_quotations - last_quotations) / max(last_quotations, 1)) * 100 if last_quotations > 0 else 0
                
                # Conversion rate
                approved_quotations = user_quotations.filter(status='approved').count()
                conversion_rate = (approved_quotations / max(user_quotations.count(), 1)) * 100
                
                # Commission (assuming 5% commission)
                commission = current_revenue * Decimal('0.05')
                commission_change = revenue_change
                
                context['sales_stats'] = {
                    'monthly_revenue': current_revenue,
                    'revenue_change': round(revenue_change, 1),
                    'monthly_orders': current_orders,
                    'orders_change': round(orders_change, 1),
                    'monthly_quotations': current_quotations,
                    'quotations_change': round(quotations_change, 1),
                    'conversion_rate': round(conversion_rate, 1),
                    'conversion_change': 2,  # Placeholder
                    'monthly_commission': commission,
                    'commission_change': round(commission_change, 1),
                }
                
                # Sales targets (placeholder)
                revenue_target = 100000  # 100K monthly target
                orders_target = 20
                quotations_target = 50
                
                context['targets'] = {
                    'revenue_target': revenue_target,
                    'revenue_percentage': min(100, (current_revenue / revenue_target) * 100) if revenue_target > 0 else 0,
                    'orders_target': orders_target,
                    'orders_percentage': min(100, (current_orders / orders_target) * 100) if orders_target > 0 else 0,
                    'quotations_target': quotations_target,
                    'quotations_percentage': min(100, (current_quotations / quotations_target) * 100) if quotations_target > 0 else 0,
                }
                
                # Pipeline data (simplified)
                context['pipeline'] = {
                    'prospects': {'count': user_quotations.filter(status='draft').count(), 'value': 0},
                    'qualified': {'count': user_quotations.filter(status='pending').count(), 'value': 0},
                    'proposal': {'count': user_quotations.filter(status='sent').count(), 'value': 0},
                    'negotiation': {'count': user_quotations.filter(status='under_review').count(), 'value': 0},
                }
                
                # Recent activities
                recent_activities = []
                
                # Recent quotations
                for quotation in user_quotations.order_by('-created_at')[:5]:
                    recent_activities.append({
                        'title': f'Quotation {quotation.quotation_number} {quotation.get_status_display()}',
                        'icon': 'fa-file-invoice',
                        'created_at': quotation.created_at,
                        'amount': quotation.total_amount if quotation.status == 'approved' else None
                    })
                
                # Recent orders
                for order in user_orders.order_by('-created_at')[:3]:
                    recent_activities.append({
                        'title': f'Order {order.order_number} {order.get_status_display()}',
                        'icon': 'fa-shopping-cart',
                        'created_at': order.created_at,
                        'amount': order.total_amount if order.status in ['completed', 'delivered', 'paid'] else None
                    })
                
                recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
                context['recent_activities'] = recent_activities[:8]
                
                # Chart data - convert Decimal objects to floats for JavaScript compatibility
                context['chart_data'] = {
                    'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    'revenue': [
                        float(current_revenue) / 4,
                        float(current_revenue) / 3,
                        float(current_revenue) / 2,
                        float(current_revenue)
                    ],
                    'orders': [current_orders//4, current_orders//3, current_orders//2, current_orders],
                }
                
            except Exception as e:
                print(f"Sales dashboard error: {e}")
                context['sales_stats'] = {
                    'monthly_revenue': 0, 'revenue_change': 0, 'monthly_orders': 0,
                    'orders_change': 0, 'monthly_quotations': 0, 'quotations_change': 0,
                    'conversion_rate': 0, 'conversion_change': 0,
                    'monthly_commission': 0, 'commission_change': 0,
                }
                context['recent_activities'] = []
        
        # CUSTOMER DASHBOARD DATA
        elif self.request.user.role == 'customer':
            try:
                user = self.request.user
                
                # Get orders using both user field and customer email for better accuracy
                orders = Order.objects.filter(
                    Q(user=user) | 
                    Q(customer__email=user.email) |
                    Q(customer__name__icontains=user.get_full_name()) |
                    Q(customer__name__icontains=user.first_name) |
                    Q(customer__name__icontains=user.last_name)
                ).distinct()
                
                # Try multiple lookup methods for quotations
                quotations = Quotation.objects.filter(
                    Q(customer__email=user.email) |
                    Q(customer__name__icontains=user.get_full_name()) |
                    Q(customer__name__icontains=user.first_name) |
                    Q(customer__name__icontains=user.last_name)
                ).distinct()
                
                # Try multiple lookup methods for projects (use 'client' not 'customer')
                projects = Project.objects.filter(
                    Q(client__email=user.email) |
                    Q(client__name__icontains=user.get_full_name()) |
                    Q(client__name__icontains=user.first_name) |
                    Q(client__name__icontains=user.last_name)
                ).distinct()
                
                # Calculate total spent from completed orders
                total_spent = orders.filter(status__in=['completed', 'delivered', 'paid']).aggregate(
                    total=Sum('total_amount')
                )['total'] or 0
                
                context['user_stats'] = {
                    'total_orders': orders.count(),
                    'total_spent': total_spent,
                    'active_projects': projects.filter(status__in=['planning', 'in_progress', 'active']).count(),
                    'pending_quotations': quotations.filter(status__in=['pending', 'draft']).count(),
                    'quotations': quotations.count(),
                    'projects': projects.count(),
                    'orders': orders.count(),
                }
                
                # Add recent activities
                recent_activities = []
                
                # Recent orders
                for order in orders.order_by('-created_at')[:5]:
                    recent_activities.append({
                        'title': f'Order {order.order_number} - {order.get_status_display()}',
                        'icon': 'fa-shopping-cart',
                        'created_at': order.created_at,
                        'amount': order.total_amount if order.status in ['completed', 'delivered', 'paid'] else None
                    })
                
                # Recent quotations
                for quotation in quotations.order_by('-created_at')[:3]:
                    recent_activities.append({
                        'title': f'Quotation {quotation.quotation_number} - {quotation.get_status_display()}',
                        'icon': 'fa-file-invoice',
                        'created_at': quotation.created_at,
                        'amount': quotation.total_amount if quotation.status == 'approved' else None
                    })
                
                # Recent projects
                for project in projects.order_by('-created_at')[:3]:
                    recent_activities.append({
                        'title': f'Project {project.project_number} - {project.get_status_display()}',
                        'icon': 'fa-project-diagram',
                        'created_at': project.created_at,
                        'amount': project.contract_value if hasattr(project, 'contract_value') and project.status == 'completed' else None
                    })
                
                # Sort activities by date and limit to latest 8
                recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
                context['recent_activities'] = recent_activities[:8]
                
            except Exception as e:
                print(f"Dashboard error: {e}")  # For debugging
                # Fallback stats if there's an error
                context['user_stats'] = {
                    'total_orders': 0,
                    'total_spent': 0,
                    'active_projects': 0,
                    'pending_quotations': 0,
                    'quotations': 0,
                    'projects': 0,
                    'orders': 0,
                }
                context['recent_activities'] = []
        
        # GENERAL DASHBOARD DATA (fallback)
        else:
            try:
                context['total_quotations'] = Quotation.objects.count()
                context['total_orders'] = Order.objects.filter(created_at__gte=current_month_start).count()
                context['total_projects'] = Project.objects.filter(status__in=['planning', 'in_progress', 'active']).count()
                context['total_revenue'] = Order.objects.filter(
                    created_at__gte=current_month_start,
                    status__in=['completed', 'delivered', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
            except Exception as e:
                print(f"General dashboard error: {e}")
                context.update({
                    'total_quotations': 0,
                    'total_orders': 0, 
                    'total_projects': 0,
                    'total_revenue': 0
                })
            
        return context

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email', 'phone', 'address']  # Fallback fields
    success_url = reverse_lazy('accounts:profile')
    
    def get_fields(self):
        """Return fields that user can edit based on their role"""
        base_fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        
        # Staff can edit additional fields but not role/security related fields
        if self.request.user.role != 'customer':
            base_fields.extend(['department'])  # Staff can update their department
        
        return base_fields
    
    def get_form(self, form_class=None):
        """Override to use dynamic fields"""
        form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        
        # Set fields dynamically
        dynamic_fields = self.get_fields()
        if hasattr(form, 'fields'):
            # Keep only the fields that are in our dynamic list
            fields_to_keep = {}
            for field_name in dynamic_fields:
                if field_name in form.fields:
                    fields_to_keep[field_name] = form.fields[field_name]
            form.fields = fields_to_keep
        
        return form
    
    def get_object(self):
        return self.request.user
    
    def get_template_names(self):
        """Return role-based profile templates"""
        user_role = self.request.user.role

        # Customer gets website-style profile
        if user_role == 'customer':
            return ['accounts/customer_profile.html']

        # All staff/management get dashboard-style profile
        staff_roles = ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person',
                      'project_manager', 'inventory_manager', 'cashier', 'technician']

        if user_role in staff_roles:
            return ['accounts/staff_profile.html']

        # Fallback - should never be reached now that all roles are covered
        return ['accounts/staff_profile.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add role-specific context
        if user.role == 'customer':
            # Customer-specific context
            context.update({
                'is_customer': True,
                'customer_stats': self.get_customer_stats(user),
            })
        else:
            # Staff-specific context
            context.update({
                'is_staff': True,
                'staff_stats': self.get_staff_stats(user),
                'department_info': self.get_department_info(user),
            })
        
        return context
    
    def get_customer_stats(self, user):
        """Get statistics for customer profile"""
        from apps.quotations.models import Quotation
        from apps.projects.models import Project
        from apps.ecommerce.models import Order
        from django.db.models import Q, Sum
        
        try:
            # Get orders using multiple lookup methods
            orders = Order.objects.filter(
                Q(user=user) | 
                Q(customer__email=user.email) |
                Q(customer__name__icontains=user.get_full_name()) |
                Q(customer__name__icontains=user.first_name) |
                Q(customer__name__icontains=user.last_name)
            ).distinct()
            
            # Get quotations using multiple lookup methods
            quotations = Quotation.objects.filter(
                Q(customer__email=user.email) |
                Q(customer__name__icontains=user.get_full_name()) |
                Q(customer__name__icontains=user.first_name) |
                Q(customer__name__icontains=user.last_name)
            ).distinct()
            
            # Get projects using multiple lookup methods (use 'client' not 'customer')
            projects = Project.objects.filter(
                Q(client__email=user.email) |
                Q(client__name__icontains=user.get_full_name()) |
                Q(client__name__icontains=user.first_name) |
                Q(client__name__icontains=user.last_name)
            ).distinct()
            
            # Calculate total spent from completed orders
            total_spent = orders.filter(status__in=['completed', 'delivered', 'paid']).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            stats = {
                'quotations': quotations.count(),
                'projects': projects.count(),
                'orders': orders.count(),
                'total_spent': total_spent,
                'active_projects': projects.filter(status__in=['planning', 'in_progress', 'active']).count(),
                'pending_quotations': quotations.filter(status__in=['pending', 'draft']).count(),
                'completed_orders': orders.filter(status__in=['completed', 'delivered', 'paid']).count(),
                'recent_orders': orders.order_by('-created_at')[:5],
                'recent_quotations': quotations.order_by('-created_at')[:5],
                'recent_projects': projects.order_by('-created_at')[:5],
            }
        except Exception as e:
            print(f"Profile stats error: {e}")  # For debugging
            stats = {
                'quotations': 0, 
                'projects': 0, 
                'orders': 0, 
                'total_spent': 0,
                'active_projects': 0,
                'pending_quotations': 0,
                'completed_orders': 0,
                'recent_orders': [],
                'recent_quotations': [],
                'recent_projects': [],
            }
        
        return stats
    
    def get_staff_stats(self, user):
        """Get statistics for staff profile"""
        from apps.quotations.models import Quotation
        from apps.projects.models import Project
        
        try:
            stats = {
                'created_quotations': Quotation.objects.filter(created_by=user).count(),
                'managed_projects': Project.objects.filter(project_manager=user).count(),
                'department': user.department or 'Not specified',
                'employee_id': user.employee_id or 'Not assigned',
            }
        except:
            stats = {'created_quotations': 0, 'managed_projects': 0, 'department': 'Not specified', 'employee_id': 'Not assigned'}
        
        return stats
    
    def get_department_info(self, user):
        """Get department information for staff"""
        return {
            'department': user.department or 'Not specified',
            'employee_id': user.employee_id or 'Not assigned',
            'hire_date': user.hire_date,
            'is_active_employee': user.is_active_employee,
        }


class ChangePasswordView(LoginRequiredMixin, View):
    def get(self, request):
        """Redirect direct URL access to profile page where change password form is located"""
        return redirect('accounts:profile')

    def post(self, request):
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        if not authenticate(username=request.user.username, password=current_password):
            return JsonResponse({
                'success': False,
                'message': 'Current password is incorrect!'
            })

        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters long!'
            })

        request.user.set_password(new_password)
        request.user.password_changed = True  # Mark password as changed
        request.user.save()

        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully!'
        })


class CustomLogoutView(View):
    """Custom logout view with role-based redirects"""
    http_method_names = ['get', 'post']
    
    def get(self, request):
        return self.logout_user(request)
    
    def post(self, request):
        return self.logout_user(request)
    
    def logout_user(self, request):
        # Check user role before logout
        is_customer = False
        user_portal = None
        if request.user.is_authenticated:
            is_customer = request.user.role == 'customer'
            user_portal = request.session.get('user_portal', 'customer')
        
        # Clear user portal preference from session
        if 'user_portal' in request.session:
            del request.session['user_portal']
        
        # Logout the user
        logout(request)
        
        # Redirect based on role with portal preference preserved
        if is_customer:
            # Customers go to homepage
            messages.success(request, 'You have been logged out successfully.')
            return redirect('core:home')
        else:
            # Staff/management go to login page with staff portal hint
            messages.info(request, 'You have been logged out. Please log in to access management functions.')
            from django.urls import reverse
            login_url = reverse('accounts:login') + '?staff=1'
            return redirect(login_url)


class RegistrationPendingView(TemplateView):
    """Show message that registration is pending email verification"""
    template_name = 'accounts/registration_pending.html'

    def dispatch(self, request, *args, **kwargs):
        """Check if user is already verified and redirect to dashboard if so"""
        # If user is authenticated and email is verified, redirect to dashboard
        if request.user.is_authenticated and hasattr(request.user, 'email_verified') and request.user.email_verified:
            messages.info(request, 'Your email is already verified. Welcome!')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)


class EmailVerificationView(View):
    """Verify email address using token"""
    
    def get(self, request, token):
        try:
            user = get_object_or_404(User, email_verification_token=token)
            
            # Check if already verified
            if user.email_verified:
                messages.info(request, 'Your email is already verified. You can log in.')
                return redirect('accounts:login')
            
            # Verify email
            user.email_verified = True
            user.is_active = True
            user.save(update_fields=['email_verified', 'is_active'])
            
            # Send welcome email
            EmailService.send_welcome_email(user)
            
            messages.success(request, 'Email verified successfully! You can now log in.')
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            messages.error(request, 'Invalid verification link.')
            return redirect('accounts:register')


class ResendVerificationView(View):
    """Resend email verification"""
    
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Email address is required.')
            return redirect('accounts:registration_pending')
        
        try:
            user = User.objects.get(email=email, email_verified=False)
            
            # Generate new token and send email
            token = user.generate_verification_token()
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': str(token)})
            )
            
            if EmailService.send_email_verification(user, verification_url):
                messages.success(request, 'Verification email sent! Please check your inbox.')
            else:
                messages.error(request, 'Failed to send verification email. Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with this email address.')
        
        return redirect('accounts:registration_pending')


class CustomerPasswordResetView(auth_views.PasswordResetView):
    """Customer password reset view"""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'emails/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        # Send custom email using our EmailService
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            # Only allow customer password reset through this URL
            if user.role != 'customer':
                messages.error(self.request, 'This email is registered as staff. Please use the staff password reset link.')
                return redirect('accounts:password_reset')
                
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode
            from apps.core.email_utils import EmailService
            
            # Generate reset URL
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send token-based email
            context = {
                'user_name': user.get_full_name() or user.username,
                'username': user.username,
                'reset_url': reset_url,
                'company_name': EmailService.get_company_context()['company_name'],
            }
            
            EmailService.send_email_notification(
                'customer_password_reset_token',
                context,
                user.email,
                f'Password Reset Request - {EmailService.get_company_context()["company_name"]}'
            )
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return redirect(self.success_url)

class StaffPasswordResetView(auth_views.PasswordResetView):
    """Staff password reset view"""
    template_name = 'accounts/password_reset_staff.html'
    email_template_name = 'emails/password_reset_staff.html'
    success_url = reverse_lazy('accounts:staff_password_reset_done')
    
    def form_valid(self, form):
        # Send custom email using our EmailService
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            # Only allow staff password reset through this URL
            staff_roles = ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person',
                         'project_manager', 'inventory_manager', 'cashier', 'technician']
            if user.role not in staff_roles:
                messages.error(self.request, 'This email is registered as a customer. Please use the customer password reset link.')
                return redirect('accounts:staff_password_reset')
                
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode
            from apps.core.email_utils import EmailService
            
            # Generate reset URL - use staff confirm URL
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse('accounts:staff_password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send token-based email
            context = {
                'user_name': user.get_full_name() or user.username,
                'username': user.username,
                'reset_url': reset_url,
                'role': user.get_role_display(),
                'company_name': EmailService.get_company_context()['company_name'],
            }
            
            EmailService.send_email_notification(
                'staff_password_reset_self',
                context,
                user.email,
                f'Password Reset Request - {EmailService.get_company_context()["company_name"]} Staff Portal'
            )
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return redirect(self.success_url)


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Customer password reset confirm view"""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

class StaffPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Staff password reset confirm view"""
    template_name = 'accounts/password_reset_confirm_staff.html'
    success_url = reverse_lazy('accounts:staff_password_reset_complete')


# Staff Management Views (Super Admin Only)
class StaffManagementView(LoginRequiredMixin, TemplateView):
    """Staff management dashboard for super admin"""
    template_name = 'accounts/staff_management.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
            
        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all staff members (exclude customers)
        staff_users = User.objects.exclude(role='customer').order_by('first_name', 'last_name')
        
        # Get role statistics with safe keys (no spaces)
        role_stats = {}
        role_counts = {}
        role_display_stats = []  # For template iteration with proper display names
        
        for role_code, role_name in User.USER_ROLES:
            if role_code != 'customer':
                count = User.objects.filter(role=role_code).count()
                role_counts[role_code] = count
                # Create safe key without spaces
                safe_key = role_name.replace(' ', '_').lower()
                role_stats[safe_key] = count
                # Add to display stats for template iteration
                role_display_stats.append({
                    'name': role_name,
                    'count': count,
                    'code': role_code
                })
        
        # Calculate combined statistics
        sales_team_count = role_counts.get('sales_manager', 0) + role_counts.get('sales_person', 0)
        technical_team_count = role_counts.get('technician', 0) + role_counts.get('project_manager', 0)
        
        context.update({
            'staff_users': staff_users,
            'role_stats': role_stats,
            'role_display_stats': role_display_stats,
            'total_staff': staff_users.count(),
            'sales_team_count': sales_team_count,
            'technical_team_count': technical_team_count,
            'role_counts': role_counts,
        })
        
        return context


class StaffCreateView(LoginRequiredMixin, CreateView):
    """Create new staff member"""
    model = User
    template_name = 'accounts/staff_create.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone',
              'employee_id', 'department', 'hire_date']
    success_url = reverse_lazy('accounts:staff_management')

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Handle AJAX request for next employee ID"""
        if request.GET.get('role') and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from apps.accounts.models import generate_employee_id
            try:
                role = request.GET.get('role')
                next_id = generate_employee_id(role)
                return JsonResponse({'employee_id': next_id})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        return super().get(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Limit role choices to staff roles only (exclude customer)
        staff_roles = [
            ('director', 'Director'),
            ('manager', 'Manager'),
            ('sales_manager', 'Sales Manager'),
            ('sales_person', 'Sales Person'),
            ('project_manager', 'Project Manager'),
            ('inventory_manager', 'Inventory Manager'),
            ('cashier', 'Cashier'),
            ('technician', 'Technician'),
        ]
        form.fields['role'].choices = staff_roles
        form.fields['role'].widget.attrs.update({'class': 'form-control'})
        
        # Add CSS classes and attributes
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['email'].widget.attrs.update({'class': 'form-control'})
        form.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        form.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        form.fields['phone'].widget.attrs.update({'class': 'form-control'})
        form.fields['employee_id'].widget.attrs.update({'class': 'form-control', 'readonly': 'readonly'})
        form.fields['department'].widget.attrs.update({'class': 'form-control'})
        form.fields['hire_date'].widget.attrs.update({'class': 'form-control', 'type': 'date'})
        
        return form
    
    def form_valid(self, form):
        user = form.save(commit=False)

        # Generate temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        user.set_password(temp_password)

        # Set as active employee
        user.is_active = True
        user.is_active_employee = True
        user.email_verified = True  # Staff emails are pre-verified
        user.password_changed = False  # Mark that user needs to change password

        user.save()
        
        # Send welcome email with login credentials
        self.send_staff_welcome_email(user, temp_password)
        
        messages.success(
            self.request, 
            f'Staff member {user.get_full_name()} created successfully. Welcome email sent with login credentials.'
        )
        
        return super().form_valid(form)
    
    def send_staff_welcome_email(self, user, temp_password):
        """Send welcome email to new staff member"""
        try:
            from apps.core.email_utils import EmailService
            
            # Create login URL
            login_url = self.request.build_absolute_uri('/accounts/login/?staff=1')
            
            context = {
                'user_name': user.get_full_name() or user.username,
                'username': user.username,
                'temporary_password': temp_password,
                'login_url': login_url,
                'role': user.get_role_display(),
                'employee_id': user.employee_id,
                'department': user.department,
            }
            
            EmailService.send_email_notification(
                'staff_welcome',
                context,
                user.email,
                f'Welcome to {EmailService.get_company_context()["company_name"]} - Staff Account Created'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'User created but welcome email failed to send: {str(e)}'
            )


class StaffDetailView(LoginRequiredMixin, DetailView):
    """View staff member details"""
    model = User
    template_name = 'accounts/staff_detail.html'
    context_object_name = 'staff_user'
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
            
        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Only allow viewing of staff members (not customers)
        return User.objects.exclude(role='customer')


class StaffToggleActiveView(LoginRequiredMixin, View):
    """Toggle staff member active status"""
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
            
        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        staff_user = get_object_or_404(User, pk=pk)
        
        # Don't allow deactivating super admins
        if staff_user.role == 'super_admin':
            messages.error(request, 'Cannot deactivate super admin accounts.')
            return redirect('accounts:staff_management')
        
        # Toggle active status
        staff_user.is_active_employee = not staff_user.is_active_employee
        staff_user.is_active = staff_user.is_active_employee
        staff_user.save()
        
        status = 'activated' if staff_user.is_active_employee else 'deactivated'
        messages.success(request, f'Staff member {staff_user.get_full_name()} has been {status}.')
        
        return redirect('accounts:staff_management')


class StaffToggleStaffStatusView(LoginRequiredMixin, View):
    """Toggle staff member Django admin access (is_staff status)"""

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        staff_user = get_object_or_404(User, pk=pk)

        # Don't allow modifying other super admins
        if staff_user.role == 'super_admin' and staff_user != request.user:
            messages.error(request, 'Cannot modify admin access for other super admin accounts.')
            return redirect('accounts:staff_management')

        # Don't allow removing staff status from customers
        if staff_user.role == 'customer':
            messages.error(request, 'Cannot grant admin access to customer accounts.')
            return redirect('accounts:staff_management')

        # Toggle staff status
        staff_user.is_staff = not staff_user.is_staff
        staff_user.save()

        status = 'granted' if staff_user.is_staff else 'revoked'
        messages.success(request, f'Django admin access has been {status} for {staff_user.get_full_name()}.')

        return redirect('accounts:staff_management')


class StaffToggleSuperuserStatusView(LoginRequiredMixin, View):
    """Toggle staff member superuser privileges (is_superuser status)"""

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        staff_user = get_object_or_404(User, pk=pk)

        # Don't allow modifying other super admins unless it's yourself
        if staff_user.role == 'super_admin' and staff_user != request.user:
            messages.error(request, 'Cannot modify superuser privileges for other super admin accounts.')
            return redirect('accounts:staff_management')

        # Don't allow granting superuser status to customers
        if staff_user.role == 'customer':
            messages.error(request, 'Cannot grant superuser privileges to customer accounts.')
            return redirect('accounts:staff_management')

        # Don't allow removing your own superuser status
        if staff_user == request.user and staff_user.is_superuser:
            messages.error(request, 'Cannot remove superuser privileges from your own account.')
            return redirect('accounts:staff_management')

        # Toggle superuser status
        staff_user.is_superuser = not staff_user.is_superuser
        staff_user.save()  # This will trigger the model's save method to handle role changes

        status = 'granted' if staff_user.is_superuser else 'revoked'
        messages.success(request, f'Superuser privileges have been {status} for {staff_user.get_full_name()}.')

        return redirect('accounts:staff_management')


class StaffEditView(LoginRequiredMixin, UpdateView):
    """Edit staff member details"""
    model = User
    template_name = 'accounts/staff_edit.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone',
              'employee_id', 'department', 'hire_date', 'salary', 'is_active_employee', 'is_staff']
    context_object_name = 'staff_user'

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the staff user object, generating employee ID if missing"""
        staff_user = super().get_object(queryset)

        # Check if this staff member needs an employee ID
        if (not staff_user.employee_id and
            staff_user.role in ['director', 'manager', 'sales_manager', 'sales_person',
                               'project_manager', 'inventory_manager', 'cashier', 'technician']):
            try:
                from apps.accounts.models import update_employee_id_on_role_change
                # Generate and assign employee ID
                update_employee_id_on_role_change(staff_user, staff_user.role)
                staff_user.save(update_fields=['employee_id'])
                # Log the assignment
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Employee ID {staff_user.employee_id} assigned to {staff_user.username} during edit form load")
            except Exception as e:
                # Log error but don't prevent form loading
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to assign employee ID for {staff_user.username}: {str(e)}")

        return staff_user

    def get_queryset(self):
        # Only allow editing of staff members (not customers)
        return User.objects.exclude(role='customer')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Prevent editing super admin role by other super admins
        staff_user = self.get_object()
        if staff_user.role == 'super_admin' and staff_user != self.request.user:
            # Remove role field if editing another super admin
            if 'role' in form.fields:
                del form.fields['role']
        else:
            # Limit role choices to staff roles only (exclude customer)
            staff_roles = [
                ('director', 'Director'),
                ('manager', 'Manager'),
                ('sales_manager', 'Sales Manager'),
                ('sales_person', 'Sales Person'),
                ('project_manager', 'Project Manager'),
                ('inventory_manager', 'Inventory Manager'),
                ('cashier', 'Cashier'),
                ('technician', 'Technician'),
            ]
            # Allow super admin role only if current user is super admin
            if self.request.user.role == 'super_admin':
                staff_roles.insert(0, ('super_admin', 'Super Admin'))

            form.fields['role'].choices = staff_roles

        # Make Employee ID read-only (IDs should never be editable)
        form.fields['employee_id'].widget.attrs.update({'readonly': 'readonly'})

        # Add CSS classes
        for field_name, field in form.fields.items():
            if field_name in ['is_active_employee', 'is_staff']:
                # Boolean fields should use form-check-input class for checkboxes
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'hire_date':
                field.widget.attrs.update({'type': 'date'})

        return form
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Staff member {form.instance.get_full_name()} updated successfully.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounts:staff_detail', kwargs={'pk': self.object.pk})


class StaffResetPasswordView(LoginRequiredMixin, View):
    """Send password reset link to staff member"""
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
            
        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        staff_user = get_object_or_404(User, pk=pk)
        
        # Ensure it's a staff member
        if staff_user.role == 'customer':
            messages.error(request, 'Cannot reset customer passwords through staff management.')
            return redirect('accounts:staff_management')
        
        # Send password reset email with token
        self.send_password_reset_email(staff_user)
        
        messages.success(
            request, 
            f'Password reset link sent to {staff_user.get_full_name()}. They will receive an email with instructions to reset their password.'
        )

        return redirect('accounts:staff_detail', pk=pk)

    def send_password_reset_email(self, user):
        """Send password reset email with token to staff member"""
        try:
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode
            from apps.core.email_utils import EmailService

            # Generate reset token and URL
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Create reset URL - use staff reset confirm URL
            reset_url = self.request.build_absolute_uri(
                reverse('accounts:staff_password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Create login URL
            login_url = self.request.build_absolute_uri('/accounts/login/?staff=1')
            
            context = {
                'user_name': user.get_full_name() or user.username,
                'username': user.username,
                'reset_url': reset_url,
                'login_url': login_url,
                'role': user.get_role_display(),
                'reset_by': self.request.user.get_full_name() or self.request.user.username,
            }
            
            EmailService.send_email_notification(
                'staff_password_reset_token',
                context,
                user.email,
                f'Password Reset Request - {EmailService.get_company_context()["company_name"]} Staff Portal'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'Password reset initiated but email failed to send: {str(e)}'
            )


class StaffResetAccountView(LoginRequiredMixin, View):
    """Reset staff member account (clear login attempts, reactivate, etc.)"""

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has super admin role
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        staff_user = get_object_or_404(User, pk=pk)

        # Ensure it's a staff member
        if staff_user.role == 'customer':
            messages.error(request, 'Cannot reset customer accounts through staff management.')
            return redirect('accounts:staff_management')

        # Don't allow resetting other super admin accounts
        if staff_user.role == 'super_admin' and staff_user != request.user:
            messages.error(request, 'Cannot reset other super admin accounts.')
            return redirect('accounts:staff_detail', pk=pk)

        # Reset account status
        staff_user.is_active = True
        staff_user.is_active_employee = True
        staff_user.email_verified = True

        # Clear any login attempt tracking (if implemented)
        # staff_user.failed_login_attempts = 0
        # staff_user.locked_until = None

        staff_user.save()

        # Send account reset notification
        self.send_account_reset_email(staff_user)

        messages.success(
            request,
            f'Account reset completed for {staff_user.get_full_name()}. Account is now active and verified.'
        )

        return redirect('accounts:staff_detail', pk=pk)

    def send_account_reset_email(self, user):
        """Send account reset notification to staff member"""
        try:
            from apps.core.email_utils import EmailService

            # Create login URL
            login_url = self.request.build_absolute_uri('/accounts/login/?staff=1')

            context = {
                'user_name': user.get_full_name() or user.username,
                'username': user.username,
                'login_url': login_url,
                'role': user.get_role_display(),
                'reset_by': self.request.user.get_full_name() or self.request.user.username,
            }

            EmailService.send_email_notification(
                'staff_account_reset',
                context,
                user.email,
                f'Account Reset - {EmailService.get_company_context()["company_name"]} Staff Portal'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'Account reset but notification email failed to send: {str(e)}'
            )


# All Users View (Super Admin & Manager Access)
class AllUsersView(LoginRequiredMixin, TemplateView):
    """User management view for super admin and managers - hierarchical permissions"""
    template_name = 'accounts/all_users.html'

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has authorized role (super admin or manager)
        if not hasattr(request.user, 'role') or request.user.role not in ['super_admin', 'manager']:
            messages.error(request, 'Access denied. Insufficient privileges.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Determine accessible roles based on user permissions
        if self.request.user.role == 'super_admin':
            # Super admin can see all users
            accessible_roles = [role[0] for role in User.USER_ROLES]
            all_users = User.objects.all().order_by('role', 'last_name', 'first_name')
        else:  # manager
            # Manager can see customers + low-ranking staff only
            accessible_roles = ['customer', 'sales_person', 'cashier', 'technician']
            all_users = User.objects.filter(role__in=accessible_roles).order_by('role', 'last_name', 'first_name')

        # Get statistics only for accessible users
        total_users = all_users.count()
        active_users = all_users.filter(is_active=True).count()
        inactive_users = all_users.filter(is_active=False).count()
        verified_users = all_users.filter(email_verified=True).count()
        unverified_users = all_users.filter(email_verified=False).count()

        # Role statistics for accessible roles only
        role_stats = {}
        role_display_data = []

        # Get counts for all roles (for display purposes), but mark inaccessible as N/A for non-super-admins
        for role_code, role_name in User.USER_ROLES:
            if role_code in accessible_roles:
                count = all_users.filter(role=role_code).count()
            else:
                count = User.objects.filter(role=role_code).count() if self.request.user.role == 'super_admin' else 0

            # Create safe key without spaces
            safe_key = role_name.replace(' ', '_').lower()
            role_stats[safe_key] = count

            # Only show accessible roles in display data, or all roles for super admin
            if role_code in accessible_roles or self.request.user.role == 'super_admin':
                role_display_data.append({
                    'code': role_code,
                    'name': role_name,
                    'count': count,
                    'accessible': role_code in accessible_roles,
                })

        # Add user role info for template logic
        context.update({
            'all_users': all_users,
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'verified_users': verified_users,
            'unverified_users': unverified_users,
            'role_stats': role_stats,
            'role_display_data': role_display_data,
            'viewer_role': self.request.user.role,
            'can_manage_staff': self.request.user.role == 'super_admin',
            'accessible_roles': accessible_roles,
        })

        return context


# Temporary debugging view - REMOVE IN PRODUCTION
def debug_role_view(request):
    """Debug user role and dashboard template selection"""
    if not request.user.is_authenticated:
        return HttpResponse("Please log in first", status=403)
    
    from django.template.loader import get_template
    
    try:
        # Get the dashboard view template selection logic
        role_templates = {
            'customer': 'accounts/customer_dashboard.html',
            'sales_person': 'accounts/sales_dashboard.html',
            'sales_manager': 'accounts/sales_dashboard.html',
            'manager': 'accounts/manager_dashboard.html',
            'super_admin': 'accounts/admin_dashboard.html',
            'project_manager': 'accounts/manager_dashboard.html',
            'inventory_manager': 'accounts/manager_dashboard.html',
            'cashier': 'accounts/sales_dashboard.html',
            'technician': 'accounts/sales_dashboard.html',
        }
        
        selected_template = role_templates.get(request.user.role, 'accounts/dashboard.html')
        
        # Check if template exists
        try:
            template = get_template(selected_template)
            template_exists = True
        except:
            template_exists = False
        
        return HttpResponse(f"""
        <h1>Role Debug Information</h1>
        <table border="1" cellpadding="5">
            <tr><td><strong>Username:</strong></td><td>{request.user.username}</td></tr>
            <tr><td><strong>Email:</strong></td><td>{request.user.email}</td></tr>
            <tr><td><strong>Role:</strong></td><td>{request.user.role}</td></tr>
            <tr><td><strong>Role Display:</strong></td><td>{request.user.get_role_display()}</td></tr>
            <tr><td><strong>Is Authenticated:</strong></td><td>{request.user.is_authenticated}</td></tr>
            <tr><td><strong>Is Staff:</strong></td><td>{request.user.is_staff}</td></tr>
            <tr><td><strong>Is Active:</strong></td><td>{request.user.is_active}</td></tr>
            <tr><td><strong>Is Active Employee:</strong></td><td>{request.user.is_active_employee}</td></tr>
            <tr><td><strong>Selected Template:</strong></td><td>{selected_template}</td></tr>
            <tr><td><strong>Template Exists:</strong></td><td>{template_exists}</td></tr>
        </table>
        <h2>Available Role Templates:</h2>
        <ul>
        {"".join(f"<li><strong>{role}:</strong> {template}</li>" for role, template in role_templates.items())}
        </ul>
        """)
        
    except Exception as e:
        import traceback
        return HttpResponse(f"""
        <h1>Role Debug Error</h1>
        <pre>{traceback.format_exc()}</pre>
        """)

def test_email_view(request):
    """Test email verification system"""
    if not request.user.is_superuser:
        return HttpResponse("Access denied", status=403)
    
    try:
        # Test company context
        context = EmailService.get_company_context()
        
        # Create test user (don't save)
        test_user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        # Test verification email
        verification_url = request.build_absolute_uri('/accounts/verify-email/test-token/')
        result = EmailService.send_email_verification(test_user, verification_url)
        
        return HttpResponse(f"""
        <h1>Email Test Results</h1>
        <p><strong>Company Context:</strong> {context}</p>
        <p><strong>Email Send Result:</strong> {result}</p>
        <p><strong>Verification URL:</strong> {verification_url}</p>
        <p>Check the console/logs for email content.</p>
        """)
        
    except Exception as e:
        import traceback
        return HttpResponse(f"""
        <h1>Email Test Error</h1>
        <pre>{traceback.format_exc()}</pre>
        """)


# Chat System Management View (Super Admin Only)
class ChatSystemManagementView(LoginRequiredMixin, TemplateView):
    """Chat system management interface for super admin dashboard"""
    template_name = 'accounts/chat_system_management.html'

    def dispatch(self, request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Check if user has chat admin permission (super_admin)
        if not has_chat_admin_permission(request.user):
            messages.error(request, 'Access denied. Chat system management requires super admin privileges.')
            return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get chat system statistics
        statistics = self.get_chat_statistics()

        # Get rooms and users for management
        all_rooms = self.get_chat_rooms()
        all_users = self.get_chat_users()
        banned_users_list = self.get_banned_users()

        context.update({
            'total_rooms': statistics['total_rooms'],
            'active_rooms': statistics['active_rooms'],
            'total_messages': statistics['total_messages'],
            'total_users_with_activity': statistics['total_users_with_activity'],
            'active_chat_users': statistics['active_chat_users'],
            'banned_users_count': statistics['banned_users'],
            'total_reactions': statistics['total_reactions'],
            'messages_with_attachments': statistics['messages_with_attachments'],
            'total_attachments_size': statistics['total_attachments_size'],
            'chat_rooms': all_rooms,
            'chat_users': all_users,
            'banned_users': banned_users_list,
            'title': 'Chat System Management',
        })

        return context

    def post(self, request, *args, **kwargs):
        """Handle form submissions for chat management actions"""
        if not has_chat_admin_permission(request.user):
            messages.error(request, 'Access denied. Chat system management requires super admin privileges.')
            return redirect('accounts:dashboard')

        action = request.POST.get('action') or request.POST.get('clear_action')
        if action:
            # Handle AJAX actions first
            if action in ['deactivate_room', 'activate_room', 'delete_room', 'ban_user', 'unban_user', 'disconnect_user']:
                return self.handle_management_action(request, action)

            # Handle form-based clear actions
            return self.handle_clear_action(request, action)

        # If no valid action, redirect back
        return redirect('accounts:chat_system_management')

    def handle_management_action(self, request, action):
        """Handle room and user management actions"""
        try:
            if action == 'deactivate_room':
                room_id = request.POST.get('room_id')
                room = get_object_or_404(ChatRoom, id=room_id)
                room.is_active = False
                room.save()
                messages.success(request, f'Room "{room.name}" has been deactivated.')

            elif action == 'activate_room':
                room_id = request.POST.get('room_id')
                room = get_object_or_404(ChatRoom, id=room_id)
                room.is_active = True
                room.save()
                messages.success(request, f'Room "{room.name}" has been activated.')

            elif action == 'delete_room':
                room_id = request.POST.get('room_id')
                room = get_object_or_404(ChatRoom, id=room_id)
                room_name = room.name
                room.delete()
                messages.success(request, f'Room "{room_name}" and all its messages have been permanently deleted.')

            elif action == 'ban_user':
                user_id = request.POST.get('user_id')
                reason = request.POST.get('reason', 'No reason specified')
                duration = request.POST.get('duration', 'permanent')

                user = get_object_or_404(User, id=user_id)

                # Calculate expiry date
                from django.utils import timezone
                expires_at = None
                if duration != 'permanent':
                    expires_at = timezone.now() + timezone.timedelta(days=int(duration))

                # Update user ban status
                user.banned_from_chat = True
                user.ban_reason = reason
                user.ban_expires_at = expires_at
                user.banned_by = request.user
                user.save()

                duration_text = "permanently" if duration == 'permanent' else f"for {duration} days"
                messages.success(request, f'User {user.username} has been banned from chat {duration_text}.')

            elif action == 'unban_user':
                user_id = request.POST.get('user_id')
                user = get_object_or_404(User, id=user_id)

                user.banned_from_chat = False
                user.ban_reason = None
                user.ban_expires_at = None
                user.banned_by = None
                user.save()

                messages.success(request, f'User {user.username} has been unbanned from chat.')

            elif action == 'disconnect_user':
                user_id = request.POST.get('user_id')
                user = get_object_or_404(User, id=user_id)

                # Force disconnect by clearing activity (this is a simplified approach)
                # In a real-time system, you would send a WebSocket message to disconnect
                UserActivity.objects.filter(user=user).delete()
                messages.success(request, f'User {user.username} has been disconnected from chat.')

        except Exception as e:
            messages.error(request, f'Error performing action: {str(e)}')

        # For AJAX requests, return JSON response
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})

        return redirect('accounts:chat_system_management')

    def get_chat_statistics(self):
        """Get chat system statistics"""
        import os
        from django.conf import settings

        # Get basic counts
        total_rooms = ChatRoom.objects.count()
        active_rooms = ChatRoom.objects.filter(is_active=True).count()
        total_messages = Message.objects.count()
        total_users_with_activity = UserActivity.objects.count()
        total_reactions = MessageReaction.objects.count()
        messages_with_attachments = Message.objects.filter(file_attachment__isnull=False).count()

        # User statistics
        active_chat_users = User.objects.filter(
            chat_rooms__is_active=True
        ).distinct().count()

        banned_users = User.objects.filter(banned_from_chat=True).count()

        # Calculate total attachments size
        total_attachments_size = self.calculate_attachments_size()

        return {
            'total_rooms': total_rooms,
            'active_rooms': active_rooms,
            'total_messages': total_messages,
            'total_users_with_activity': total_users_with_activity,
            'active_chat_users': active_chat_users,
            'banned_users': banned_users,
            'total_reactions': total_reactions,
            'messages_with_attachments': messages_with_attachments,
            'total_attachments_size': total_attachments_size,
        }

    def calculate_attachments_size(self):
        """Calculate total size of all chat attachments"""
        import os
        from django.conf import settings

        total_size = 0
        attachment_dir = os.path.join(settings.MEDIA_ROOT, 'chat_attachments')

        if os.path.exists(attachment_dir):
            for root, dirs, files in os.walk(attachment_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass

        return self.format_bytes(total_size)

    def format_bytes(self, bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"

    def handle_clear_action(self, request, action):
        """Handle the different clear actions from the management interface"""
        from django.db import transaction

        try:
            with transaction.atomic():
                if action == 'all':
                    # Clear everything
                    cleared_data = self.clear_all_data()
                    messages.success(request, f"Successfully cleared all chat data from the system: {cleared_data}.")

                elif action == 'messages':
                    # Clear messages only
                    cleared_messages = self.clear_all_messages()
                    messages.success(request, f"Successfully cleared all messages from all rooms: {cleared_messages} messages deleted.")

                elif action == 'attachments':
                    # Clear attachments only
                    cleared_attachments = self.clear_all_attachments()
                    messages.success(request, f"Successfully cleared all file attachments: {cleared_attachments} files deleted.")

                elif action == 'activity':
                    # Clear activity only
                    cleared_activity = self.clear_all_activity()
                    messages.success(request, f"Successfully cleared all user activity data: {cleared_activity} records deleted.")

        except Exception as e:
            messages.error(request, f"Error during clear operation: {str(e)}")

        return redirect('accounts:chat_system_management')

    def clear_all_data(self):
        """Clear all chat data (messages, attachments, activity, preferences)"""
        messages_cleared = self.clear_all_messages()
        attachments_cleared = self.clear_all_attachments()
        activity_cleared = self.clear_all_activity()
        preferences_cleared = self.clear_all_preferences()

        return f"{messages_cleared} messages, {attachments_cleared} files, {activity_cleared} activity records, {preferences_cleared} preferences"

    def clear_all_messages(self):
        """Clear all messages and related data"""
        messages = Message.objects.all()
        reaction_count = MessageReaction.objects.all().delete()[0]
        read_status_count = MessageReadStatus.objects.all().delete()[0]

        message_count = messages.delete()[0]
        return message_count + reaction_count + read_status_count

    def clear_all_attachments(self):
        """Clear all file attachments"""
        import os
        from django.conf import settings

        deleted_count = 0
        attachment_dir = os.path.join(settings.MEDIA_ROOT, 'chat_attachments')

        messages_with_attachments = Message.objects.filter(file_attachment__isnull=False)
        for message in messages_with_attachments:
            if message.file_attachment and message.file_attachment.name:
                file_path = os.path.join(settings.MEDIA_ROOT, str(message.file_attachment))
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    # Log error but continue
                    print(f"Failed to delete attachment {file_path}: {e}")

            # Clear the file field
            message.file_attachment = None
            message.file_name = None
            message.save()

        # Clean up empty directories
        if os.path.exists(attachment_dir) and not os.listdir(attachment_dir):
            try:
                os.rmdir(attachment_dir)
            except:
                pass

        return deleted_count

    def clear_all_activity(self):
        """Clear all user activity data"""
        return UserActivity.objects.all().delete()[0]

    def clear_all_preferences(self):
        """Clear all notification preferences"""
        return NotificationPreference.objects.all().delete()[0]

    def get_chat_rooms(self):
        """Get all chat rooms for management display"""
        return ChatRoom.objects.select_related('created_by').order_by('-created_at')[:50]

    def get_chat_users(self):
        """Get all users who have participated in chat for management"""
        from django.db.models import Exists, OuterRef

        # Get users who have messages or are in activity table
        users_with_messages = User.objects.filter(
            Exists(Message.objects.filter(author=OuterRef('pk')))
        ).distinct()

        users_with_activity = User.objects.filter(
            Exists(UserActivity.objects.filter(user=OuterRef('pk')))
        ).distinct()

        # Combine and annotate with message counts
        from django.db.models import Count, Q, Prefetch

        users = User.objects.filter(
            Q(Exists(Message.objects.filter(author=OuterRef('pk')))) |
            Q(Exists(UserActivity.objects.filter(user=OuterRef('pk'))))
        ).distinct().annotate(
            message_count=Count('messages', distinct=True)
        ).prefetch_related(
            Prefetch('chat_activity', queryset=UserActivity.objects.all())
        ).order_by('-message_count')[:50]

        return users

    def get_banned_users(self):
        """Get all users banned from chat"""
        from django.utils import timezone

        banned_users = User.objects.filter(banned_from_chat=True).select_related('banned_by').order_by('-date_joined')
        current_time = timezone.now()

        # Annotate with ban status
        banned_list = []
        for user in banned_users:
            status = "Permanent" if not user.ban_expires_at else \
                     "Active" if user.ban_expires_at > current_time else \
                     "Expired"
            banned_list.append({
                'user': user,
                'status': status,
                'banned_by': user.banned_by,
                'expires_at': user.ban_expires_at,
                'reason': user.ban_reason or "No reason specified",
            })

        return banned_list


class TogglePortalView(View):
    """Toggle between customer and staff portal"""

    def get(self, request):
        return redirect('accounts:login')
