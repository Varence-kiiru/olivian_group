from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'account'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html', next_page='account:dashboard'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),

    # Password Reset URLs
    # Update the PasswordResetView configuration
     path('password-reset/',
          auth_views.PasswordResetView.as_view(
          template_name='account/password_reset.html',
          success_url=reverse_lazy('account:password_reset_done'),
          email_template_name='account/password_reset_email.html'
          ),
          name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'),
         name='password_reset_done'),
     path('password-reset-confirm/<uidb64>/<token>/',
          auth_views.PasswordResetConfirmView.as_view(
          template_name='account/password_reset_confirm.html',
          success_url=reverse_lazy('account:password_reset_complete')
          ),
          name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # Password Change URLs
    path('password-change/',
         auth_views.PasswordChangeView.as_view(template_name='account/password_change.html'),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='account/password_change_done.html'),
         name='password_change_done'),
]
