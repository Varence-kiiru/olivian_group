from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('system/health/', views.SystemHealthView.as_view(), name='system_health'),
    path('cart/count/', views.CartCountAPIView.as_view(), name='cart_count_api'),
    path('coverage-check/', views.CoverageCheckAPIView.as_view(), name='api_coverage_check'),
]
