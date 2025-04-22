from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('staff/', views.staff_chat_dashboard, name='staff_dashboard'),
    path('api/init-chat/', views.InitChatView.as_view(), name='init_chat'),
    path('api/send-message/', views.SendMessageView.as_view(), name='send_message'),
    path('api/sessions/<str:session_id>/', views.ChatSessionDetailView.as_view(), name='session_detail'),
    path('api/sessions/<str:session_id>/mark-read/', views.MarkMessagesReadView.as_view(), name='mark_read'),
]
