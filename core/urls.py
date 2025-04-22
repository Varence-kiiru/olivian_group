from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('change-language/', views.change_language, name='change_language'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    path('newsletter/confirm/<str:token>/', views.confirm_subscription, name='confirm_subscription'),
    path('quote/request/', views.quote_request, name='quote_request'),
    path('about/', views.about, name='about'),
    path('privacy-policy/', views.policy_page, {'policy_type': 'privacy'}, name='privacy_policy'),
    path('terms-conditions/', views.policy_page, {'policy_type': 'terms'}, name='terms_conditions'),
    path('return-refund-policy/', views.policy_page, {'policy_type': 'refund'}, name='refund_policy'),
    path('shipping-delivery/', views.policy_page, {'policy_type': 'shipping'}, name='shipping_policy'),
    path('faqs/', views.faqs, name='faqs'),
    path('environmental-commitment/', views.policy_page, {'policy_type': 'environment'}, name='environmental_commitment'),
    path('certifications-standards/', views.certifications, name='certifications'),
    path('returns-refunds/', views.policy_page, {'policy_type': 'refund'}, name='returns_refunds'),
    path('sustainability/', views.policy_page, {'policy_type': 'environment'}, name='sustainability'),
    path('certifications/', views.certifications, name='certifications_short'),
]

