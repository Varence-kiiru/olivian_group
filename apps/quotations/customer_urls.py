from django.urls import path
from . import views

app_name = 'quotations_customer'

urlpatterns = [
    # Customer-facing solar calculator (no authentication required)
    path('', views.SolarCalculatorView.as_view(), name='calculator'),
    path('generate-quotation/', views.GenerateQuotationFromCalculatorView.as_view(), name='generate_quotation'),
    path('schedule-consultation/', views.ScheduleConsultationView.as_view(), name='schedule_consultation'),
    
    # Customer quotation views (no authentication required)
    path('quotation/<str:quotation_number>/', views.CustomerQuotationView.as_view(), name='view'),
    path('quotation/<str:quotation_number>/pdf/', views.CustomerQuotationPDFView.as_view(), name='pdf'),
]
