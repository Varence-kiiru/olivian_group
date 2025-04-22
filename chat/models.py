from django.db import models
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatSession(models.Model):
    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4)
    visitor_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions')
    user_name = models.CharField(max_length=255, blank=True, null=True)
    user_email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Chat with {self.user.get_full_name() or self.user.username}"
        elif self.user_name:
            return f"Chat with {self.user_name}"
        else:
            return f"Chat {self.id} - {self.visitor_id}"
    
    def get_display_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        elif self.user_name:
            return self.user_name
        else:
            return f"Visitor #{self.id[:8]}"
    
    def unread_count(self):
        return self.messages.filter(sender='visitor', is_read=False).count()

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    message = models.TextField()
    sender = models.CharField(max_length=20)  # 'visitor' or 'agent'
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"
    
    def save(self, *args, **kwargs):
        # Auto-mark agent messages as read
        if self.sender == 'agent':
            self.is_read = True
        super().save(*args, **kwargs)
