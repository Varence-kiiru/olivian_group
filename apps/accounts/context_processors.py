def user_portal_context(request):
    """
    Add user portal context to all templates
    """
    context = {
        'user_portal': 'guest',
        'is_staff_portal': False,
        'is_customer_portal': False,
    }
    
    if request.user.is_authenticated:
        staff_roles = ['super_admin', 'manager', 'sales_manager', 'sales_person', 
                      'project_manager', 'inventory_manager', 'cashier', 'technician']
        
        if request.user.role in staff_roles:
            context.update({
                'user_portal': 'staff',
                'is_staff_portal': True,
                'is_customer_portal': False,
            })
        else:
            context.update({
                'user_portal': 'customer',
                'is_staff_portal': False,
                'is_customer_portal': True,
            })
    else:
        # Check URL parameters for guest users
        staff_param = request.GET.get('staff')
        if staff_param == '1':
            context.update({
                'user_portal': 'staff_guest',
                'is_staff_portal': True,
                'is_customer_portal': False,
            })
        else:
            context.update({
                'user_portal': 'customer_guest',
                'is_staff_portal': False,
                'is_customer_portal': True,
            })
    
    return context
