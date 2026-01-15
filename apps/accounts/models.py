from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import uuid

# Role abbreviation mapping for employee IDs
ROLE_ABBREVIATIONS = {
    'super_admin': 'ADM',
    'director': 'DIR',
    'manager': 'MGR',
    'sales_manager': 'SMG',
    'sales_person': 'SPN',
    'project_manager': 'PMG',
    'inventory_manager': 'IMG',
    'cashier': 'CSR',
    'technician': 'TEC',
}

def generate_employee_id(role):
    """
    Generate a unique employee ID for the given role.
    Format: OG/{ROLE_ABBR}/{SEQUENTIAL_NUMBER}

    Uses database locking to prevent race conditions when multiple users
    are created simultaneously.
    """
    if role not in ROLE_ABBREVIATIONS:
        raise ValueError(f"Invalid role: {role}")

    abbr = ROLE_ABBREVIATIONS[role]

    # Use database transaction with row locking to prevent race conditions
    from django.db import transaction
    from django.db.models import Max

    with transaction.atomic():
        # Lock all existing employee IDs for this role to prevent concurrent access
        # We use select_for_update() to ensure atomicity
        locked_queryset = User.objects.filter(
            role=role,
            employee_id__startswith=f'OG/{abbr}/'
        ).exclude(employee_id__exact='').select_for_update()

        # Force evaluation of the queryset to acquire the lock
        existing_count = locked_queryset.count()

        if existing_count == 0:
            # No existing IDs for this role
            next_number = 1
        else:
            # Get the highest existing number - parse all IDs to find the true maximum
            role_ids = list(locked_queryset.values_list('employee_id', flat=True))
            numbers = []

            for emp_id in role_ids:
                try:
                    parts = emp_id.split('/')
                    if len(parts) >= 3:
                        numbers.append(int(parts[2]))
                except (ValueError, IndexError):
                    continue

            if numbers:
                next_number = max(numbers) + 1
            else:
                # Fallback if parsing fails for all existing IDs
                next_number = 1

    return f'OG/{abbr}/{next_number:03d}'

def update_employee_id_on_role_change(user, new_role):
    """
    Update employee ID when role changes or when assigning ID to existing staff.
    """
    # Only assign IDs to staff roles (not customers)
    if new_role not in ROLE_ABBREVIATIONS:
        return

    current_abbr = None
    if user.employee_id and user.employee_id.startswith('OG/'):
        parts = user.employee_id.split('/')
        if len(parts) >= 2:
            current_abbr = parts[1]

    # If changing roles or doesn't have an ID, generate new one
    if current_abbr != ROLE_ABBREVIATIONS[new_role] or not user.employee_id:
        user.employee_id = generate_employee_id(new_role)

class User(AbstractUser):
    USER_ROLES = [
        ('super_admin', 'Super Admin'),
        ('director', 'Director'),
        ('manager', 'Manager'),
        ('sales_manager', 'Sales Manager'),
        ('sales_person', 'Sales Person'),
        ('project_manager', 'Project Manager'),
        ('inventory_manager', 'Inventory Manager'),
        ('cashier', 'Cashier'),
        ('customer', 'Customer'),
        ('technician', 'Technician'),
    ]
    
    role = models.CharField(max_length=20, choices=USER_ROLES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, help_text="Short bio about the user")
    date_of_birth = models.DateField(blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=50, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    is_active_employee = models.BooleanField(default=True)

    # Social media links
    facebook_url = models.URLField(blank=True, help_text="Facebook profile URL")
    twitter_url = models.URLField(blank=True, help_text="Twitter profile URL")
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    instagram_url = models.URLField(blank=True, help_text="Instagram profile URL")
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # Password change tracking
    password_changed = models.BooleanField(default=True, help_text="Whether user has changed from temporary password")

    # Chat system restrictions
    banned_from_chat = models.BooleanField(default=False, help_text="Whether user is banned from using the chat system")
    banned_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='banned_users')
    ban_reason = models.TextField(blank=True, help_text="Reason for chat ban")
    ban_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the chat ban expires (null = permanent)")

    # Customer specific fields
    customer_type = models.CharField(
        max_length=20,
        choices=[
            ('individual', 'Individual'),
            ('business', 'Business'),
            ('government', 'Government'),
        ],
        default='individual'
    )
    company_name = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        if self.get_full_name():
            return f"{self.get_full_name()} ({self.username})"
        return self.username
    
    def get_display_name(self):
        if self.role == 'customer' and self.company_name:
            return self.company_name
        return self.get_full_name() or self.username
    
    def has_role_permission(self, permission):
        """Check if user's role has specific permission"""
        role_permissions = {
            'super_admin': ['*'],
            'director': ['view_reports', 'manage_projects', 'approve_budgets', 'manage_staff', 'strategic_planning'],
            'manager': ['view_reports', 'manage_projects', 'approve_budgets', 'manage_staff'],
            'sales_manager': ['manage_quotations', 'view_sales_reports', 'manage_customers'],
            'sales_person': ['create_quotations', 'view_products', 'manage_leads'],
            'project_manager': ['manage_projects', 'view_budgets', 'manage_tasks'],
            'inventory_manager': ['manage_inventory', 'create_purchase_orders', 'view_stock_reports'],
            'cashier': ['pos_sales', 'view_products', 'manage_customers'],
            'customer': ['view_products', 'create_orders', 'view_projects'],
            'technician': ['view_projects', 'update_tasks', 'view_manuals']
        }

        user_permissions = role_permissions.get(self.role, [])
        return '*' in user_permissions or permission in user_permissions
    
    def save(self, *args, **kwargs):
        """Override save to automatically assign super_admin role to superusers"""
        # Automatically set role to super_admin and verify email for superusers created via terminal
        if self.is_superuser and self.role == 'customer':
            self.role = 'super_admin'
            self.email_verified = True  # Superusers are pre-verified
            self.is_active = True  # Ensure superusers are active

        # Call parent save method
        super().save(*args, **kwargs)

    def generate_verification_token(self):
        """Generate a new email verification token"""
        self.email_verification_token = uuid.uuid4()
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    notification_preferences = models.JSONField(default=dict)
    language_preference = models.CharField(
        max_length=5,
        choices=[('en', 'English'), ('sw', 'Swahili'), ('fr', 'French'), ('ar', 'Arabic')],
        default='en'
    )
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    
    def __str__(self):
        return f"{self.user.username} Profile"

class PrivacyConsent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consent_type = models.CharField(max_length=50)
    consented = models.BooleanField(default=False)
    consent_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        unique_together = ('user', 'consent_type')
