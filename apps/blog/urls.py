from django.urls import path
from . import views

app_name = 'blog'

# Staff management URLs
staff_patterns = [
    path('management/', views.blog_management_dashboard, name='management_dashboard'),
    path('management/posts/', views.post_management_list, name='post_list'),
    path('management/posts/create/', views.post_create, name='post_create'),
    path('management/posts/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('management/posts/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('management/posts/<int:pk>/preview/', views.post_preview, name='post_preview'),
    path('management/posts/<int:pk>/toggle-status/', views.toggle_post_status, name='toggle_post_status'),
    path('management/posts/<int:pk>/toggle-featured/', views.toggle_post_featured, name='toggle_post_featured'),
    path('management/categories/', views.category_management_list, name='category_list'),
    path('management/categories/create/', views.category_create, name='category_create'),
    path('management/categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('management/categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('management/categories/export/', views.category_export, name='category_export'),
    path('management/tags/', views.tag_management_list, name='tag_list'),
    path('management/tags/create/', views.tag_create, name='tag_create'),
    path('management/tags/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    path('management/tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),
    path('management/tags/export/', views.tag_export, name='tag_export'),
    path('management/comments/', views.comment_management_list, name='comment_list'),
    path('management/comments/<int:pk>/approve/', views.approve_comment, name='approve_comment'),
    path('management/comments/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('management/banner/', views.banner_management, name='banner_management'),
    path('management/banner/<int:pk>/toggle/', views.toggle_banner_status, name='toggle_banner_status'),
    # API endpoint for post search (for CKEditor internal linking)
    path('api/search-posts/', views.search_posts_api, name='search_posts_api'),
]

# Public URLs
public_patterns = [
    path('', views.blog_list, name='blog'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('tag/<slug:slug>/', views.tag_posts, name='tag_posts'),
    path('<slug:slug>/like/', views.like_post, name='like_post'),
    path('<slug:slug>/comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
]

urlpatterns = staff_patterns + public_patterns
