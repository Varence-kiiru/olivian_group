from django.urls import path, include
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat dashboard and rooms
    path('', views.chat_dashboard, name='dashboard'),
    path('room/<slug:room_name>/', views.chat_room, name='room'),

    # Room management
    path('room/<slug:room_name>/members/', views.room_members, name='room_members'),
    path('room/<slug:room_name>/edit/', views.edit_room, name='edit_room'),
    path('room/<slug:room_name>/delete/', views.delete_room, name='delete_room'),
    path('create/', views.create_room, name='create_room'),

    # User settings
    path('settings/', views.user_settings, name='user_settings'),

    # API endpoints
    path('api/room/<slug:room_name>/send/', views.api_send_message, name='api_send_message'),
    path('api/room/<slug:room_name>/messages/', views.api_room_messages, name='api_room_messages'),
    path('api/room/<slug:room_name>/info/', views.api_room_info, name='api_room_info'),
    path('api/room/<slug:room_name>/typing/', views.api_get_typing_users, name='api_get_typing_users'),
    path('api/room/<slug:room_name>/typing/start/', views.api_start_typing, name='api_start_typing'),
    path('api/typing/stop/', views.api_stop_typing, name='api_stop_typing'),
    path('api/search/', views.api_search_messages, name='api_search_messages'),
    path('api/message/<int:message_id>/react/', views.api_toggle_reaction, name='api_toggle_reaction'),
    path('api/message/<int:message_id>/reactions/', views.api_message_reactions, name='api_message_reactions'),
    path('api/online-users/', views.api_online_users, name='api_online_users'),
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/messages/global/', views.api_messages_global, name='api_messages_global'),
]
