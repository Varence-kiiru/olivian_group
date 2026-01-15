import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageReadStatus
from django.utils.text import slugify

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat functionality"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Check if user is authenticated
        if self.scope['user'] and self.scope['user'].is_authenticated:
            self.user = self.scope['user']
        else:
            await self.close()
            return

        # Check if user has access to this room
        can_access = await self.can_access_room(self.room_name)
        if not can_access:
            await self.close()
            return

        # Get or create room
        self.room = await self.get_room(self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send message history to new connection
        await self.send_messages_history()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            content = text_data_json.get('content', '')

            if message_type == 'message':
                # Handle chat message
                if content.strip():
                    message = await self.save_message(content)

                    # Send message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': {
                                'id': message.id,
                                'content': message.content,
                                'author': message.author.username,
                                'author_full_name': f"{message.author.first_name} {message.author.last_name}".strip() or message.author.username,
                                'author_id': message.author.id,
                                'author_role': message.author.get_role_display(),
                                'timestamp': message.timestamp.isoformat(),
                                'room_id': message.room.id,
                                'is_edited': message.is_edited,
                            },
                            'sender': self.user.id
                        }
                    )
            elif message_type == 'mark_read':
                # Handle read status updates
                message_id = text_data_json.get('message_id')
                if message_id:
                    await self.mark_message_as_read(message_id)

                # Notify online users about read status
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_read_message',
                        'message_id': message_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                    }
                )

        except json.JSONDecodeError:
            # Handle invalid JSON
            await self.send(text_data=json.dumps({
                'error': 'Invalid message format'
            }))

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        message = event['message']
        message['type'] = 'message'

        # Don't send message back to sender
        if event.get('sender') != self.user.id:
            await self.send(text_data=json.dumps(message))

    async def user_read_message(self, event):
        """Send read status update to WebSocket"""
        data = {
            'type': 'read_status',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
        }
        await self.send(text_data=json.dumps(data))

    @database_sync_to_async
    def can_access_room(self, room_name):
        """Check if user can access the room"""
        try:
            room = ChatRoom.objects.get(name=room_name, is_active=True)
            user = self.scope['user']

            if room.room_type == 'private':
                return room.participants.filter(id=user.id).exists()
            elif room.room_type == 'department':
                # Check if user belongs to appropriate groups using slug-exact match
                room_slug = slugify(room.name)
                user_group_slugs = {slugify(g.name) for g in user.groups.all()}
                return room_slug in user_group_slugs or user.is_staff
            elif room.room_type == 'general':
                # General rooms are accessible to all authenticated users
                return True
            elif room.room_type == 'project':
                # Check project access (management/staff or slug-exact match)
                room_slug = slugify(room.name)
                user_group_slugs = {slugify(g.name) for g in user.groups.all()}
                return user.groups.filter(name__in=['management', 'staff']).exists() or room_slug in user_group_slugs or user.is_staff
            return True
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def get_room(self, room_name):
        """Get or create chat room"""
        room, created = ChatRoom.objects.get_or_create(
            name=room_name,
            defaults={'room_type': 'general', 'created_by': self.scope['user']}
        )
        return room

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        return Message.objects.create(
            room=self.room,
            author=self.user,
            content=content
        )

    async def send_messages_history(self):
        """Send recent messages to newly connected user"""
        messages = await database_sync_to_async(self._get_messages)()

        # Send messages in chronological order
        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'message',
                'id': message.id,
                'content': message.content,
                'author': message.author.username,
                'author_full_name': f"{message.author.first_name} {message.author.last_name}".strip() or message.author.username,
                'author_id': message.author.id,
                'author_role': message.author.get_role_display(),
                'timestamp': message.timestamp.isoformat(),
                'room_id': message.room.id,
                'is_edited': message.is_edited,
            }))

    def _get_messages(self):
        """Get recent messages from database"""
        return list(Message.objects.filter(
            room=self.room
        ).select_related('author').order_by('timestamp')[:50])

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark a message as read by the current user"""
        try:
            message = Message.objects.get(id=message_id, room=self.room)
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=self.user,
                defaults={'read_at': message.timestamp}
            )
        except Message.DoesNotExist:
            pass


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for tracking online status"""

    @database_sync_to_async
    def mark_user_online(self):
        """Mark user as online in database"""
        from .models import UserActivity
        return UserActivity.mark_user_online(self.scope['user'])

    async def connect(self):
        if self.scope['user'] and self.scope['user'].is_authenticated:
            self.user = self.scope['user']

            # Update user activity in database
            await self.mark_user_online()

            await self.channel_layer.group_add(
                'online_users',
                self.channel_name
            )
            await self.accept()

            # Notify others that user is online
            await self.channel_layer.group_send(
                'online_users',
                {
                    'type': 'user_online',
                    'user_id': self.user.id,
                    'username': self.user.username,
                }
            )

    async def disconnect(self, close_code):
        if hasattr(self, 'user'):
            await self.channel_layer.group_discard(
                'online_users',
                self.channel_name
            )

            # Notify others that user is offline
            await self.channel_layer.group_send(
                'online_users',
                {
                    'type': 'user_offline',
                    'user_id': self.user.id,
                    'username': self.user.username,
                }
            )

    async def user_online(self, event):
        """Handle user coming online"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps(event))

    async def user_offline(self, event):
        """Handle user going offline"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps(event))


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for dashboard realtime updates (presence, unread counts)"""

    async def connect(self):
        if self.scope['user'] and self.scope['user'].is_authenticated:
            self.user = self.scope['user']

            # Join global online users group to receive presence events
            await self.channel_layer.group_add('online_users', self.channel_name)

            # Join all room groups the user has access to so we can forward unread updates
            room_names = await database_sync_to_async(self._get_accessible_room_names)()
            for rn in room_names:
                await self.channel_layer.group_add(f'chat_{rn}', self.channel_name)

            await self.accept()

            # Send initial state: online users list and initial unread counts
            await self.send_initial_state()

    async def disconnect(self, close_code):
        if hasattr(self, 'user'):
            await self.channel_layer.group_discard('online_users', self.channel_name)
            room_names = await database_sync_to_async(self._get_accessible_room_names)()
            for rn in room_names:
                await self.channel_layer.group_discard(f'chat_{rn}', self.channel_name)

    async def chat_message(self, event):
        """Receive message events from room groups and forward minimal info for dashboard"""
        message = event.get('message') or {}
        room_id = message.get('room_id')
        room_name = None
        if room_id:
            # Try to include room name for client-side mapping
            try:
                from .models import ChatRoom
                room = await database_sync_to_async(ChatRoom.objects.filter(id=room_id).values_list('name', flat=True).first)()
                room_name = room
            except Exception:
                room_name = None

        payload = {
            'type': 'chat_message',
            'room_name': room_name or event.get('room'),
            'message': {
                'id': message.get('id'),
                'content': (message.get('content') or '')[:140],
                'author': message.get('author'),
                'timestamp': message.get('timestamp'),
            }
        }
        await self.send(text_data=json.dumps(payload))

    async def user_online(self, event):
        await self.send(text_data=json.dumps({ 'type': 'user_online', 'user_id': event.get('user_id'), 'username': event.get('username') }))

    async def user_offline(self, event):
        await self.send(text_data=json.dumps({ 'type': 'user_offline', 'user_id': event.get('user_id'), 'username': event.get('username') }))

    async def send_initial_state(self):
        """Send initial online users and unread placeholders"""
        from .models import UserActivity
        # Send online users
        def _online_dicts():
            qs = UserActivity.get_online_users()
            out = []
            for a in qs:
                out.append({'id': a.user.id, 'username': a.user.username, 'display_name': (a.user.get_full_name() or a.user.username)})
            return out
        online_users = await database_sync_to_async(_online_dicts)()
        await self.send(text_data=json.dumps({'type': 'initial_online', 'online_users': online_users}))

        # Send initial unread counts per room (computed server-side)
        unread = await database_sync_to_async(self._get_unread_counts)()
        await self.send(text_data=json.dumps({'type': 'initial_unread', 'counts': unread}))

    def _get_accessible_room_names(self):
        """Return list of room names the current user can access (sync helper)"""
        user = self.scope['user']
        qs = ChatRoom.objects.filter(is_active=True)
        # General rooms always included
        names = set(qs.filter(room_type='general').values_list('name', flat=True))
        # Private rooms where user is a participant
        names.update(qs.filter(room_type='private', participants=user).values_list('name', flat=True))
        # Department/project rooms by group slug match or management/staff
        user_group_slugs = {slugify(g.name) for g in user.groups.all()}
        for room in qs.filter(room_type__in=['department', 'project']):
            if slugify(room.name) in user_group_slugs or user.groups.filter(name__in=['management', 'staff']).exists() or user.is_staff:
                names.add(room.name)
        return list(names)

    def _get_unread_counts(self):
        """Return dict of unread counts per room name for the user"""
        from .models import Message, MessageReadStatus
        counts = {}
        for room in ChatRoom.objects.filter(is_active=True):
            total = Message.objects.filter(room=room).count()
            read = MessageReadStatus.objects.filter(message__room=room, user=self.scope['user']).count()
            unread = max(0, total - read)
            if unread > 0:
                counts[room.name] = unread
        return counts
