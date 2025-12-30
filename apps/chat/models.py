from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class ChatRoom(models.Model):
    """Represents a chat room for different departments, projects, or general communication"""

    ROOM_TYPES = [
        ('department', 'Department'),
        ('project', 'Project'),
        ('general', 'General'),
        ('private', 'Private'),
    ]

    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='general')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms')

    # For project-specific rooms
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True)

    # For private rooms (direct messaging)
    participants = models.ManyToManyField(User, related_name='chat_rooms', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    def get_participants_count(self):
        """Return the number of participants in the room"""
        if self.room_type == 'private':
            return self.participants.count()
        elif self.room_type == 'department':
            return User.objects.filter(
                groups__in=self.get_department_groups()
            ).count()
        elif self.room_type == 'general':
            # General rooms are accessible to all authenticated users
            return User.objects.filter(is_active=True).count()
        return self.participants.count()

    def get_department_groups(self):
        """Return groups associated with this room"""
        from django.contrib.auth.models import Group
        return Group.objects.filter(name__icontains=self.name.lower())


class Message(models.Model):
    """Represents a message in a chat room"""

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    # Reply functionality
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    # For file attachments
    file_attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)

    # Message meta
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    # @mentions tracking
    mentioned_users = models.ManyToManyField(User, related_name='mentioned_in_messages', blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        truncated_content = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.author.username}: {truncated_content}"

    def save(self, *args, **kwargs):
        # Track message edits
        if self.pk:
            self.is_edited = True
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)

        # Extract and save mentions (only for new or updated messages)
        self.extract_mentions()

    def extract_mentions(self):
        """Extract @mentions from message content and populate mentioned_users field"""
        if not self.content:
            return

        import re
        # Match @ followed by word characters (letters, digits, underscore)
        # This matches patterns like @john, @user123, @john_doe
        mentions = re.findall(r'@(\w+)', self.content)

        if mentions:
            # Get unique usernames and find corresponding user objects
            unique_mentions = set(mentions)
            mentioned_users = User.objects.filter(username__in=unique_mentions)
            self.mentioned_users.set(mentioned_users)
        else:
            # Clear mentions if content has no @mentions
            self.mentioned_users.clear()


class MessageReadStatus(models.Model):
    """Tracks which users have read which messages"""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['message', 'user']
        verbose_name = 'Message Read Status'
        verbose_name_plural = 'Message Read Statuses'

    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"


class NotificationPreference(models.Model):
    """User preferences for chat notifications"""

    NOTIFICATION_TYPES = [
        ('all', 'All Messages'),
        ('mentions', 'Mentions Only'),
        ('none', 'None'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_preferences')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='all')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


class MessageReaction(models.Model):
    """Tracks emoji reactions to messages"""

    COMMON_EMOJIS = [
        ('👍', 'thumbs_up'),
        ('❤️', 'heart'),
        ('😂', 'joy'),
        ('👎', 'thumbs_down'),
        ('😮', 'astonished'),
        ('🎉', 'party'),
        ('😢', 'cry'),
        ('😡', 'angry'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    emoji = models.CharField(max_length=10, choices=COMMON_EMOJIS)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['message', 'user', 'emoji']
        ordering = ['created_at']
        verbose_name = 'Message Reaction'
        verbose_name_plural = 'Message Reactions'

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"

    @classmethod
    def get_reaction_summary(cls, message):
        """Get a summary of reactions for a message"""
        reactions = cls.objects.filter(message=message).select_related('user')
        summary = {}

        for reaction in reactions:
            if reaction.emoji not in summary:
                summary[reaction.emoji] = {
                    'count': 0,
                    'users': []
                }
            summary[reaction.emoji]['count'] += 1
            summary[reaction.emoji]['users'].append(reaction.user)

        return summary


class UserActivity(models.Model):
    """Tracks user online activity for chat system"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_activity')
    last_activity = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)

    # Typing indicator fields
    is_typing = models.BooleanField(default=False)
    typing_in_room = models.ForeignKey(ChatRoom, null=True, blank=True, on_delete=models.SET_NULL, related_name='typing_users')
    last_typing_update = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

    def update_activity(self):
        """Update user's last activity timestamp"""
        now = timezone.now()
        self.last_activity = now
        self.is_online = True
        self.save()

    @classmethod
    def get_online_users(cls):
        """Get users who have been active within the last 10 minutes"""
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        return cls.objects.filter(
            last_activity__gte=ten_minutes_ago,
            is_online=True
        ).select_related('user')

    @classmethod
    def mark_user_online(cls, user):
        """Mark a user as online and update their activity"""
        activity, created = cls.objects.get_or_create(
            user=user,
            defaults={'last_activity': timezone.now(), 'is_online': True}
        )
        if not created:
            if activity.last_activity < timezone.now() - timedelta(minutes=1):
                # Only update if it's been more than a minute to reduce database writes
                activity.update_activity()
        return activity

    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
