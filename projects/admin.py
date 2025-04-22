from django.contrib import admin
from .models import ProjectCategory, Project, ProjectImage, Testimonial, ProjectsBanner
from core.admin import admin_site  # Import with the correct name

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1

class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 1

@admin.register(ProjectsBanner)
class ProjectsBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
   
    def has_add_permission(self, request):
        # Allow only one instance of projects banner
        if self.model.objects.exists():
            return False
        return True

@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'client', 'start_date', 'is_featured')
    list_filter = ('status', 'category', 'is_featured', 'start_date')
    search_fields = ('title', 'client', 'location', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline, TestimonialInline]
    date_hierarchy = 'start_date'
   
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'client', 'location', 'status', 'is_featured')
        }),
        ('Dates', {
            'fields': ('start_date', 'completion_date')
        }),
        ('Project Details', {
            'fields': ('description', 'challenge', 'solution', 'result', 'main_image', 'duration')
        }),
    )

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_company', 'project', 'rating', 'date')
    list_filter = ('rating', 'date')
    search_fields = ('client_name', 'client_company', 'content')

# Register models with the custom admin site
admin_site.register(ProjectsBanner, ProjectsBannerAdmin)
admin_site.register(ProjectCategory, ProjectCategoryAdmin)
admin_site.register(Project, ProjectAdmin)
admin_site.register(Testimonial, TestimonialAdmin)

# If you need to register ProjectImage separately
@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'image', 'caption')
    list_filter = ('project',)
    search_fields = ('project__title', 'caption')

# Register ProjectImage with custom admin site
admin_site.register(ProjectImage, ProjectImageAdmin)
