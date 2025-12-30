from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Leads
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/create/', views.LeadCreateView.as_view(), name='lead_create'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_update'),
    path('leads/<int:pk>/delete/', views.LeadDeleteView.as_view(), name='lead_delete'),
    path('leads/<int:pk>/convert/', views.ConvertLeadView.as_view(), name='lead_convert'),

    # Opportunities
    path('opportunities/', views.OpportunityListView.as_view(), name='opportunity_list'),
    path('opportunities/create/', views.OpportunityCreateView.as_view(), name='opportunity_create'),
    path('opportunities/<int:pk>/', views.OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', views.OpportunityUpdateView.as_view(), name='opportunity_update'),
    path('opportunities/<int:pk>/delete/', views.OpportunityDeleteView.as_view(), name='opportunity_delete'),
    path('opportunities/<int:pk>/change-stage/', views.change_opportunity_stage, name='opportunity_change_stage'),

    # Contacts
    path('contacts/', views.ContactListView.as_view(), name='contact_list'),
    path('contacts/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_update'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),

    # Companies
    path('companies/', views.CompanyListView.as_view(), name='company_list'),
    path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('companies/<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<int:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    path('companies/<int:pk>/export/', views.CompanyExportView.as_view(), name='company_export'),

    # Activities
    path('activities/', views.ActivityListView.as_view(), name='activity_list'),
    path('activities/create/', views.ActivityCreateView.as_view(), name='activity_create'),
    path('activities/<int:pk>/', views.ActivityDetailView.as_view(), name='activity_detail'),
    path('activities/<int:pk>/edit/', views.ActivityUpdateView.as_view(), name='activity_update'),
    path('activities/<int:pk>/delete/', views.ActivityDeleteView.as_view(), name='activity_delete'),

    # Campaigns
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', views.CampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('campaigns/<int:pk>/edit/', views.CampaignUpdateView.as_view(), name='campaign_update'),
    path('campaigns/<int:pk>/delete/', views.CampaignDeleteView.as_view(), name='campaign_delete'),

    # Pipeline
    path('pipeline/', views.PipelineView.as_view(), name='pipeline'),
    path('opportunities/<int:pk>/move/', views.OpportunityMoveView.as_view(), name='opportunity_move'),
    path('pipeline/export/', views.PipelineExportView.as_view(), name='pipeline_export'),

    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('reports/export/', views.ExportReportView.as_view(), name='export_report'),
    path('reports/sales-forecast/', views.SalesForecastView.as_view(), name='sales_forecast'),
    path('reports/lead-conversion/', views.LeadConversionView.as_view(), name='lead_conversion'),

    # API endpoints for AJAX
    path('api/leads/by-status/', views.LeadsByStatusAPIView.as_view(), name='api_leads_by_status'),
    path('api/opportunities/forecast/', views.OpportunityForecastAPIView.as_view(), name='api_opportunity_forecast'),
    
    # Lead Sources
    path('lead-sources/', views.LeadSourceListView.as_view(), name='lead_source_list'),
    path('lead-sources/create/', views.LeadSourceCreateView.as_view(), name='lead_source_create'),
    path('lead-sources/<int:pk>/', views.LeadSourceDetailView.as_view(), name='lead_source_detail'),
    path('lead-sources/<int:pk>/edit/', views.LeadSourceUpdateView.as_view(), name='lead_source_edit'),
    path('lead-sources/<int:pk>/delete/', views.LeadSourceDeleteView.as_view(), name='lead_source_delete'),

    # API Companies
    path('api/companies/<int:pk>/', views.CompanyDetailAPIView.as_view(), name='company_api_detail'),
    
    # API Activities
    path('api/activities/calendar/', views.ActivityCalendarEventsView.as_view(), name='activity_calendar_events'),

    # Team Assignment
    path('api/team/assign/', views.TeamAssignmentView.as_view(), name='team_assign'),

    # Email Templates
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email_template_list'),
    path('email-templates/create/', views.EmailTemplateCreateView.as_view(), name='email_template_create'),
    path('email-templates/<int:pk>/', views.EmailTemplateDetailView.as_view(), name='email_template_detail'),
    path('email-templates/<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='email_template_update'),
    path('email-templates/<int:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='email_template_delete'),
    path('email-templates/<int:pk>/test/', views.test_email_template, name='email_template_test'),

    # Email Composer
    path('email-composer/', views.EmailComposerView.as_view(), name='email_composer'),
]
