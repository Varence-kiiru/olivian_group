from django.contrib import admin
from django.utils import timezone
from .models import Category, Tag, Post, Comment, BlogBanner

@admin.register(BlogBanner)
class BlogBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
   
    def has_add_permission(self, request):
        # Limit to one banner for simplicity
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'views')
    list_filter = ('status', 'category', 'author', 'is_featured')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('views',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'category', 'tags', 'content')
        }),
        ('SEO & Social Sharing', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'featured_image'),
            'description': 'Optimize for search engines and social media sharing'
        }),
        ('Publishing', {
            'fields': ('status', 'excerpt', 'is_featured', 'canonical_url')
        }),
        ('Analytics', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
    )
   
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'post', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('name', 'email', 'content')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"
