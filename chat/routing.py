from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Use only one pattern with a more flexible regex
    re_path(r'^ws/chat/(?P<session_id>[\w-]+)/?$', consumers.ChatConsumer.as_asgi()),
]

print(f"WebSocket URL patterns registered: {websocket_urlpatterns}")
