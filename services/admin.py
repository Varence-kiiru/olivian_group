from django.contrib import admin
from .models import Service, ServiceBenefit, ServicesBanner
from core.admin import admin_site  # Import with the correct name

@admin.register(ServicesBanner)
class ServicesBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle']
   
    def has_add_permission(self, request):
        # Allow only one instance of services banner
        if self.model.objects.exists():
            return False
        return True

class ServiceBenefitInline(admin.TabularInline):
    model = ServiceBenefit
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ServiceBenefitInline]
    ordering = ['order']

# Register your models with the custom admin site
admin_site.register(ServicesBanner, ServicesBannerAdmin)
admin_site.register(Service, ServiceAdmin)

# If you need to register ServiceBenefit separately
@admin.register(ServiceBenefit)
class ServiceBenefitAdmin(admin.ModelAdmin):
    list_display = ['service', 'title', 'order']
    list_filter = ['service']
    search_fields = ['title', 'description']
    ordering = ['order']

# Register ServiceBenefit with custom admin site
admin_site.register(ServiceBenefit, ServiceBenefitAdmin)
