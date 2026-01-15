import os
import django
import json

import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.chat.models import ChatRoom, Message
from django.test import Client

User = get_user_model()

# Create or get users
poll_username = 'poll_user'
sender_username = 'sender_user'

poll_user, created = User.objects.get_or_create(username=poll_username, defaults={'email': 'poll@example.com'})
if created:
    poll_user.set_password('pollpass')
    poll_user.save()

sender_user, created = User.objects.get_or_create(username=sender_username, defaults={'email': 'sender@example.com'})
if created:
    sender_user.set_password('senderpass')
    sender_user.save()

# Create or get room
room_name = 'test-poll-room'
room, created = ChatRoom.objects.get_or_create(name=room_name, defaults={'room_type': 'general', 'created_by': poll_user})

# Create a message by sender_user
msg = Message.objects.create(room=room, author=sender_user, content='Automated test message for polling.')
print('Created message id:', msg.id)

# Use Django test client to simulate poll_user calling the global messages endpoint
client = Client()
client.force_login(poll_user)
resp = client.get('/chat/api/messages/global/', HTTP_HOST='127.0.0.1:8000')
print('Response status:', resp.status_code)
try:
    payload = resp.json()
    print('Payload:', json.dumps(payload, indent=2, ensure_ascii=False))
except Exception as e:
    print('Failed to parse JSON response:', e)
    print(resp.content)
