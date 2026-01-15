from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Email verification
    path('registration-pending/', views.RegistrationPendingView.as_view(), name='registration_pending'),
    path('verify-email/<uuid:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),

    # Password reset - Customer
    path('password-reset/', views.CustomerPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),

    # Password reset - Staff
    path('staff/password-reset/', views.StaffPasswordResetView.as_view(), name='staff_password_reset'),
    path('staff/password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done_staff.html'), name='staff_password_reset_done'),
    path('staff/password-reset/<uidb64>/<token>/', views.StaffPasswordResetConfirmView.as_view(), name='staff_password_reset_confirm'),
    path('staff/password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete_staff.html'), name='staff_password_reset_complete'),
    
    # Staff management (Super Admin only)
    path('staff/', views.StaffManagementView.as_view(), name='staff_management'),
    path('staff/create/', views.StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/edit/', views.StaffEditView.as_view(), name='staff_edit'),
    path('staff/<int:pk>/toggle-active/', views.StaffToggleActiveView.as_view(), name='staff_toggle_active'),
    path('staff/<int:pk>/toggle-staff-status/', views.StaffToggleStaffStatusView.as_view(), name='staff_toggle_staff_status'),
    path('staff/<int:pk>/toggle-superuser-status/', views.StaffToggleSuperuserStatusView.as_view(), name='staff_toggle_superuser_status'),
    path('staff/<int:pk>/reset-password/', views.StaffResetPasswordView.as_view(), name='staff_reset_password'),
    path('staff/<int:pk>/reset-account/', views.StaffResetAccountView.as_view(), name='staff_reset_account'),

    # All users management (Super Admin only)
    path('users/', views.AllUsersView.as_view(), name='all_users'),

    # Chat system management (Super Admin only)
    path('chat-management/', views.ChatSystemManagementView.as_view(), name='chat_system_management'),

    # Temporary test URL - REMOVE IN PRODUCTION
    path('test-email/', views.test_email_view, name='test_email'),
    path('debug-role/', views.debug_role_view, name='debug_role'),
]
