# Test script to simulate a push subscription and trigger a Message post_save signal
import os
import sys
import time

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.chat.models import ChatRoom, PushSubscription, Message
from django.utils import timezone
from django.conf import settings

User = get_user_model()

print('Starting test_push script')

# Create two users
sender, created = User.objects.get_or_create(username='push_sender', defaults={'email':'push_sender@example.com', 'first_name':'Push', 'last_name':'Sender'})
receiver, created = User.objects.get_or_create(username='push_receiver', defaults={'email':'push_receiver@example.com', 'first_name':'Push', 'last_name':'Receiver'})

# Create or get a room and ensure both users are participants
room, _ = ChatRoom.objects.get_or_create(name='test-push-room', defaults={'room_type':'private', 'created_by': sender})
room.participants.add(sender)
room.participants.add(receiver)

# Create a fake push subscription for receiver
fake_endpoint = 'https://example.com/fake_push_endpoint/12345'
fake_p256dh = 'BOrandomp256dhBase64string=='
fake_auth = 'randomAuth=='

sub, created = PushSubscription.objects.update_or_create(
    user=receiver,
    endpoint=fake_endpoint,
    defaults={'p256dh': fake_p256dh, 'auth': fake_auth}
)
print('Created push subscription for', receiver.username)

# Create a message authored by sender — should trigger post_save signal and attempt to send push
msg = Message.objects.create(room=room, author=sender, content='Test push message from script', timestamp=timezone.now())
print('Created message id', msg.id)

# Give threads a moment to run
print('Waiting 5 seconds for background send attempts...')
time.sleep(5)
print('Done.')
