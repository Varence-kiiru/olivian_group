from django.urls import path
from .forms import CustomerRequirementsWizard
from . import views

app_name = 'quotations'

urlpatterns = [
    path('', views.QuotationListView.as_view(), name='list'),
    path('dashboard/', views.QuotationDashboardView.as_view(), name='dashboard'),

    # Public customer quotation request form
    path('request/', views.CustomerQuotationRequestView.as_view(), name='request_form'),
    path('request-success/', views.QuotationRequestSuccessView.as_view(), name='request_success'),

    # Quotation requests management (staff only)
    path('requests/', views.QuotationRequestListView.as_view(), name='requests_list'),
    path('requests/<int:pk>/', views.QuotationRequestDetailView.as_view(), name='request_detail'),

    # Check new requests (AJAX)
    path('check-new-requests/', views.CheckNewRequestsView.as_view(), name='check_new_requests'),

    # Bulk actions for requests
    path('bulk-actions/', views.BulkActionsView.as_view(), name='bulk_actions'),

    # Quotation management views
    path('create/', views.QuotationCreateView.as_view(), name='create'),
    path('create-from-request/<int:request_pk>/', views.QuotationCreateFromRequestView.as_view(), name='create_from_request'),
    path('create-from-requirements/', views.CreateQuotationFromRequirementsView.as_view(), name='create_from_requirements'),
    path('create-from-calculator/', views.CreateFromCalculatorView.as_view(), name='create_from_calculator'),

    # Calculator replaced with request system
    path('calculator/', views.CustomerQuotationRequestView.as_view(), name='calculator'),  # Redirect calculator to request form
    path('calculator/generate-quotation/', views.GenerateQuotationFromCalculatorView.as_view(), name='generate_quotation'),
    path('calculator/schedule-consultation/', views.ScheduleConsultationView.as_view(), name='schedule_consultation'),

    # Enhanced quotation tools
    path('product-selector/', views.ProductSelectorView.as_view(), name='product_selector'),
    path('builder/', views.QuotationBuilderView.as_view(), name='builder'),
    path('requirements/', CustomerRequirementsWizard.as_view(), name='customer_requirements'),
    path('enhanced-analytics/', views.EnhancedAnalyticsView.as_view(), name='enhanced_analytics'),

    # Export and bulk operations
    path('export/', views.QuotationExportView.as_view(), name='export'),
    path('bulk-actions/', views.QuotationBulkActionsView.as_view(), name='bulk_actions'),
    path('analytics/', views.QuotationAnalyticsView.as_view(), name='analytics'),

    # Customer-facing views (no login required)
    path('view/<str:quotation_number>/', views.CustomerQuotationView.as_view(), name='customer_view'),
    path('view/<str:quotation_number>/pdf/', views.CustomerQuotationPDFView.as_view(), name='customer_pdf'),

    # Follow-up views
    path('follow-ups/', views.QuotationFollowUpListView.as_view(), name='follow_up_list'),
    path('follow-up/<int:pk>/complete/', views.complete_follow_up, name='complete_follow_up'),

    # Management views (login required)
    path('<str:quotation_number>/', views.QuotationDetailView.as_view(), name='detail'),
    path('<str:quotation_number>/edit/', views.QuotationUpdateView.as_view(), name='edit'),
    path('<str:quotation_number>/pdf/', views.QuotationPDFView.as_view(), name='pdf'),
    path('<str:quotation_number>/delete/', views.QuotationDeleteView.as_view(), name='delete'),
    path('<str:quotation_number>/convert/', views.ConvertToSaleView.as_view(), name='convert_to_sale'),
    path('<str:quotation_number>/send/', views.QuotationSendEmailView.as_view(), name='send_email'),
    path('<str:quotation_number>/duplicate/', views.QuotationDuplicateView.as_view(), name='duplicate'),
    path('<str:quotation_number>/convert/', views.ConvertToSaleView.as_view(), name='convert'),  # Add this line
    path('<str:quotation_number>/follow-up/', views.QuotationFollowUpView.as_view(), name='follow_up'),
]
