from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile, PrivacyConsent

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'customer_type')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'company_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Organization', {
            'fields': ('role', 'department', 'employee_id')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address', 'profile_picture', 'bio')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('Customer Information', {
            'fields': ('customer_type', 'company_name', 'tax_number', 'credit_limit')
        }),
        ('Employment Information', {
            'fields': ('salary', 'hire_date', 'is_active_employee')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'manager':
            return qs.filter(department=request.user.department)
        return qs

    def save_model(self, request, obj, form, change):
        """
        Override save_model to ensure employee IDs are assigned when roles change in admin.
        """
        if change:  # Only for existing users
            # Store original role before saving
            try:
                original_user = User.objects.get(pk=obj.pk)
                obj._original_role = original_user.role
            except User.DoesNotExist:
                obj._original_role = None

        # Save the user
        super().save_model(request, obj, form, change)

        # Manually trigger employee ID assignment if role changed
        if hasattr(obj, '_original_role') and obj._original_role != obj.role:
            from apps.accounts.models import update_employee_id_on_role_change
            update_employee_id_on_role_change(obj, obj.role)
            obj.save(update_fields=['employee_id'])  # Save the updated employee_id

    def get_form(self, request, obj=None, **kwargs):
        """
        Override get_form to ensure employee_id field gets proper help text
        """
        form = super().get_form(request, obj, **kwargs)
        if 'employee_id' in form.base_fields:
            form.base_fields['employee_id'].help_text = (
                "Auto-generated for staff roles. Format: OG/{ROLE_ABBR}/{NUMBER}. "
                "Leave blank for automatic assignment."
            )
        return form

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'language_preference', 'timezone', 'theme_preference')
    list_filter = ('language_preference', 'theme_preference')
    search_fields = ('user__username', 'user__email')

@admin.register(PrivacyConsent)
class PrivacyConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'consented', 'consent_date')
    list_filter = ('consent_type', 'consented', 'consent_date')
    readonly_fields = ('consent_date', 'ip_address')
