from django.contrib import admin
from .models import Contact, ContactPageContent
from core.admin import admin_site  # Import with the correct name

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"
    
    actions = ['mark_as_read']

@admin.register(ContactPageContent)
class ContactPageContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'email', 'phone')
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True

#Register models with the custom admin site
admin_site.register(Contact, ContactAdmin)
admin_site.register(ContactPageContent, ContactPageContentAdmin)
