"""
Middleware for password change enforcement
"""

class PasswordChangeMiddleware:
    """
    Middleware to enforce password change for users with temporary passwords
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that should be accessible without password change
        self.allowed_urls = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/change-password/',
            '/admin/login/',
            '/admin/logout/',
            '/api/',
        ]

    def __call__(self, request):
        # Check if user is authenticated and is staff
        if request.user.is_authenticated:
            staff_roles = ['super_admin', 'manager', 'sales_manager', 'sales_person',
                          'project_manager', 'inventory_manager', 'cashier', 'technician']

            # If user is staff and hasn't changed password yet
            if (hasattr(request.user, 'role') and
                request.user.role in staff_roles and
                not getattr(request.user, 'password_changed', True)):

                # Check if current URL is allowed
                current_path = request.path_info
                is_allowed = any(current_path.startswith(url) for url in self.allowed_urls)

                # If not allowed, redirect to password change
                if not is_allowed:
                    from django.shortcuts import redirect
                    from django.contrib import messages
                    messages.warning(request, 'Please change your temporary password before accessing other features.')
                    return redirect('accounts:change_password')

        response = self.get_response(request)
        return response
