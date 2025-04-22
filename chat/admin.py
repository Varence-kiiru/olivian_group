from django.contrib import admin
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('message', 'sender', 'timestamp', 'is_read')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'visitor_id', 'is_active', 'created_at', 'unread_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('id', 'visitor_id')
    readonly_fields = ('id', 'visitor_id', 'created_at', 'updated_at')
    inlines = [ChatMessageInline]
    
    def unread_count(self, obj):
        return obj.unread_count()
    unread_count.short_description = 'Unread Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'short_message', 'is_read', 'timestamp')
    list_filter = ('sender', 'is_read', 'timestamp')
    search_fields = ('message', 'session__id', 'session__visitor_id')
    readonly_fields = ('session', 'timestamp')
    
    def short_message(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    short_message.short_description = 'Message'
