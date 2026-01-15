from django import template
from django.template.loader import get_template
from apps.accounts.models import User

register = template.Library()

@register.simple_tag(takes_context=True)
def get_user_base_template(context, email=None):
    """
    Determine the appropriate base template based on user role
    Returns the base template name for staff or customer
    """
    request = context.get('request')
    
    # If user is logged in, use their role
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
        return get_base_template_for_role(user.role)
    
    # If email is provided, look up user role
    if email:
        try:
            user = User.objects.get(email=email)
            return get_base_template_for_role(user.role)
        except User.DoesNotExist:
            pass
    
    # Check for staff parameter in request
    if request and request.GET.get('staff'):
        return 'accounts/auth_base_staff.html'
    
    # Default to customer base
    return 'accounts/auth_base.html'

def get_base_template_for_role(role):
    """
    Map user roles to appropriate base templates
    """
    staff_roles = [
        'super_admin', 'manager', 'sales_manager', 'sales_person', 
        'project_manager', 'inventory_manager', 'cashier', 'technician'
    ]
    
    if role in staff_roles:
        return 'accounts/auth_base_staff.html'
    else:
        return 'accounts/auth_base.html'

@register.simple_tag
def is_staff_role(role):
    """
    Check if a role is a staff role
    """
    staff_roles = [
        'super_admin', 'manager', 'sales_manager', 'sales_person', 
        'project_manager', 'inventory_manager', 'cashier', 'technician'
    ]
    return role in staff_roles

@register.filter
def user_base_template(user):
    """
    Filter to get base template for a user
    Usage: {{ user|user_base_template }}
    """
    if not user or not hasattr(user, 'role'):
        return 'accounts/auth_base.html'
    
    return get_base_template_for_role(user.role)
