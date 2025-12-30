from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('api/notifications/', views.NotificationAPIView.as_view(), name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),

    # Newsletter subscription
    path('newsletter/subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),

    # Newsletter Dashboard (Management)
    path('dashboard/newsletter/', views.NewsletterDashboardView.as_view(), name='newsletter_dashboard'),
    path('dashboard/newsletter/campaigns/', views.NewsletterCampaignListView.as_view(), name='newsletter_campaign_list'),
    path('dashboard/newsletter/campaigns/create/', views.NewsletterCampaignCreateView.as_view(), name='newsletter_campaign_create'),
    path('dashboard/newsletter/campaigns/<int:pk>/', views.NewsletterCampaignDetailView.as_view(), name='newsletter_campaign_detail'),
    path('dashboard/newsletter/campaigns/<int:pk>/edit/', views.NewsletterCampaignUpdateView.as_view(), name='newsletter_campaign_update'),
    path('dashboard/newsletter/campaigns/<int:pk>/send/', views.NewsletterCampaignSendView.as_view(), name='newsletter_campaign_send'),
    path('dashboard/newsletter/subscribers/', views.NewsletterSubscriberListView.as_view(), name='newsletter_subscriber_list'),
    path('dashboard/newsletter/subscribers/<int:pk>/', views.NewsletterSubscriberDetailView.as_view(), name='newsletter_subscriber_detail'),
    path('dashboard/newsletter/subscribers/<int:pk>/toggle/', views.NewsletterSubscriberToggleView.as_view(), name='newsletter_subscriber_toggle'),

    # Newsletter tracking
    path('newsletter/track/open/<int:log_id>/', views.TrackEmailOpenView.as_view(), name='track_open'),
    path('newsletter/track/click/<int:log_id>/', views.TrackEmailClickView.as_view(), name='track_click'),
    path('newsletter/unsubscribe/<str:token>/<int:subscriber_id>/', views.UnsubscribeView.as_view(), name='unsubscribe'),

    # Legal Documents
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('how-to-delete-your-data/', views.DataDeletionView.as_view(), name='data_deletion'),
    path('disclaimer/', views.DisclaimerView.as_view(), name='disclaimer'),
    path('refund-policy/', views.RefundPolicyView.as_view(), name='refund_policy'),
    path('legal/<str:doc_type>/', views.LegalDocumentView.as_view(), name='legal_document'),

    # Cookie management
    path('cookie-preferences/', views.CookiePreferencesView.as_view(), name='cookie_preferences'),
    path('cookie-policy/', views.CookiePolicyView.as_view(), name='cookie_policy'),
    path('api/cookie-consent/status/', views.cookie_consent_status, name='cookie_consent_status'),
    path('api/cookie-consent/update/', views.update_cookie_consent, name='update_cookie_consent'),
    path('api/cookie-categories/', views.cookie_categories_api, name='cookie_categories_api'),

    # Test notifications (development/debugging)
    path('test-notifications/', views.NotificationTestView.as_view(), name='test_notifications'),

    # API endpoints
    path('api/system/status/', views.SystemStatusAPIView.as_view(), name='api_system_status'),
    path('api/system/health/', views.SystemHealthCheckAPIView.as_view(), name='api_health_check'),
    path('api/financial-stats/', views.FinancialStatsAPIView.as_view(), name='api_financial_stats'),

    # System Administration URLs
    path('system/backup/', views.SystemBackupView.as_view(), name='system_backup'),
    path('system/maintenance/', views.SystemMaintenanceView.as_view(), name='system_maintenance'),
    path('system/reports/', views.SystemReportsView.as_view(), name='system_reports'),
    path('system/logs/', views.SystemLogsView.as_view(), name='system_logs'),
    path('system/clear-cache/', views.ClearCacheView.as_view(), name='clear_cache'),
    path('system/run-diagnostics/', views.RunDiagnosticsView.as_view(), name='run_diagnostics'),

    # Export URLs
    path('export/all-data/', views.ExportAllDataView.as_view(), name='export_all_data'),
    path('export/user-report/', views.ExportUserReportView.as_view(), name='export_user_report'),
    path('export/system-report/', views.ExportSystemReportView.as_view(), name='export_system_report'),
    path('export/financial-report/', views.ExportFinancialReportView.as_view(), name='export_financial_report'),
    path('export/financial-data-csv/', views.ExportFinancialCSVView.as_view(), name='export_financial_csv'),

    # Service Area Management URLs
    path('service-areas/', views.ServiceAreaListView.as_view(), name='service_area_list'),
    path('service-areas/create/', views.ServiceAreaCreateView.as_view(), name='service_area_create'),
    path('service-areas/<int:pk>/', views.ServiceAreaDetailView.as_view(), name='service_area_detail'),
    path('service-areas/<int:pk>/edit/', views.ServiceAreaUpdateView.as_view(), name='service_area_edit'),
    path('service-areas/<int:pk>/delete/', views.ServiceAreaDeleteView.as_view(), name='service_area_delete'),
    path('service-areas/bulk-update/', views.ServiceAreaBulkUpdateView.as_view(), name='service_area_bulk_update'),
]
