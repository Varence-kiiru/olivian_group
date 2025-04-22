from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, UserPreferences
from core.admin import admin_site # Import the custom admin site instance

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

class PreferencesInline(admin.StackedInline):
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'Preferences'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, PreferencesInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

# Unregister User from the default admin site
admin.site.unregister(User)
# Register User with the default admin site
admin.site.register(User, UserAdmin)

# Register with the custom admin site - use the instance, not the class
admin_site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'company', 'created_at')
    search_fields = ('user__username', 'phone', 'company')
    list_filter = ('created_at',)

@admin.register(UserPreferences)
class PreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'newsletter_subscription', 'language')
    list_filter = ('email_notifications', 'newsletter_subscription', 'language')

# Register these models with the custom admin site too
admin_site.register(Profile, ProfileAdmin)
admin_site.register(UserPreferences, PreferencesAdmin)
