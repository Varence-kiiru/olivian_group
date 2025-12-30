from django.urls import path, re_path
from . import views

app_name = 'products'

urlpatterns = [
    # Management URLs (for staff) - must come first to avoid slug conflicts
    path('manage/', views.ProductManagementListView.as_view(), name='manage'),
    path('manage/add/', views.ProductCreateView.as_view(), name='create'),
    path('manage/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='update'),
    path('share-facebook/<slug:slug>/', views.ProductFacebookShareView.as_view(), name='share_facebook'),

    # Customer-facing URLs
    path('', views.ProductListView.as_view(), name='list'),
    path('category/<slug:slug>/', views.ProductCategoryView.as_view(), name='category'),
    re_path(r'^(?P<slug>[-a-zA-Z0-9_.]+)/$', views.ProductDetailView.as_view(), name='detail'),
]
