from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings
import os

from .models import (
    ChatRoom, Message, MessageReaction, MessageReadStatus,
    UserActivity, NotificationPreference
)


def has_chat_admin_permission(user):
    """Check if user has permission to manage chat system (superuser or super_admin role)"""
    return user.is_superuser or (hasattr(user, 'role') and user.role == 'super_admin')


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'is_active', 'is_auto_join', 'created_at', 'created_by', 'participants_count']
    list_filter = ['room_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'created_by']
    ordering = ['-created_at']

    actions = ['clear_room_messages', 'clear_room_attachments']

    def participants_count(self, obj):
        return obj.get_participants_count()
    participants_count.short_description = "Participants"

    def clear_room_messages(self, request, queryset):
        """Clear all messages from selected rooms"""
        if not has_chat_admin_permission(request.user):
            messages.error(request, "Only super administrators can perform this action.")
            return

        total_messages = 0
        total_deleted = 0

        for room in queryset:
            count = room.messages.count()
            total_messages += count

        if total_messages == 0:
            messages.warning(request, "No messages found in selected rooms.")
            return

        # Confirm action
        if 'confirm_clear' in request.POST:
            with transaction.atomic():
                for room in queryset:
                    # Delete messages and related data
                    messages = list(room.messages.all())
                    for message in messages:
                        # Delete reactions
                        message.reactions.all().delete()
                        # Delete read statuses
                        message.read_status.all().delete()

                        # Delete attachments
                        if message.file_attachment and message.file_attachment.name:
                            file_path = os.path.join(settings.MEDIA_ROOT, str(message.file_attachment))
                            try:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                            except Exception as e:
                                self.message_user(
                                    request,
                                    f"Failed to delete attachment for message {message.id}: {e}",
                                    level=messages.WARNING
                                )

                        message.delete()
                        total_deleted += 1

            messages.success(
                request,
                f"Cleared {total_deleted} messages from {queryset.count()} rooms."
            )

        else:
            # Show confirmation page
            message_text = f"You are about to clear {total_messages} messages from {queryset.count()} rooms. This action cannot be undone."
            context = {
                'title': 'Confirm Clear Messages',
                'message_text': message_text,
                'action_name': 'clear_room_messages',
                'action_desc': 'Clear Messages',
                'queryset': queryset,
                'opts': self.opts,
            }
            return admin.site.admin_view(self.confirm_clear_view)(request, context)

    clear_room_messages.short_description = "Clear messages from selected rooms"

    def clear_room_attachments(self, request, queryset):
        """Clear all attachments from selected rooms"""
        if not has_chat_admin_permission(request.user):
            messages.error(request, "Only super administrators can perform this action.")
            return

        total_attachments = 0

        for room in queryset:
            count = room.messages.filter(file_attachment__isnull=False).count()
            total_attachments += count

        if total_attachments == 0:
            messages.warning(request, "No attachments found in selected rooms.")
            return

        if 'confirm_clear_attachments' in request.POST:
            deleted_files = 0
            with transaction.atomic():
                for room in queryset:
                    messages = room.messages.filter(file_attachment__isnull=False)
                    for message in messages:
                        if message.file_attachment and message.file_attachment.name:
                            file_path = os.path.join(settings.MEDIA_ROOT, str(message.file_attachment))
                            try:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    deleted_files += 1
                                    # Clear the file field
                                    message.file_attachment = None
                                    message.file_name = None
                                    message.save()
                            except Exception as e:
                                self.message_user(
                                    request,
                                    f"Failed to delete attachment for message {message.id}: {e}",
                                    level=messages.WARNING
                                )

            messages.success(
                request,
                f"Deleted {deleted_files} attachment files from {queryset.count()} rooms."
            )

        else:
            # Show confirmation
            message_text = f"You are about to delete {total_attachments} attachment files from {queryset.count()} rooms."
            context = {
                'title': 'Confirm Clear Attachments',
                'message_text': message_text,
                'action_name': 'clear_room_attachments',
                'action_desc': 'Clear Attachments',
                'queryset': queryset,
                'opts': self.opts,
            }
            return admin.site.admin_view(self.confirm_clear_view)(request, context)

    clear_room_attachments.short_description = "Clear attachments from selected rooms"

    def confirm_clear_view(self, request, context):
        """Custom confirmation view for destructive actions"""
        from django.shortcuts import render
        from django.template.response import TemplateResponse

        return TemplateResponse(request, 'chat/admin/chat_confirm_clear.html', context)

    def has_add_permission(self, request):
        # Only allow staff to add rooms
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        # Only superuser can delete rooms
        return has_chat_admin_permission(request.user)

    # Custom admin methods for department room management
    def get_list_display(self, request):
        display = super().get_list_display(request)
        if request.user.is_staff:
            display = list(display) + ['manage_members_link']
        return display

    def manage_members_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        if obj.room_type in ['private', 'project']:
            url = reverse('admin:chat_chatroom_change', args=[obj.pk])
            return format_html('<a href="{}#participants">Manage Members</a>', url)
        elif obj.room_type == 'department':
            # Department rooms use groups - show group management
            return format_html('<a href="/admin/auth/group/" target="_blank">Manage Groups</a>')
        return "N/A"
    manage_members_link.short_description = "Members"
    manage_members_link.allow_tags = True


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'author', 'truncated_content', 'timestamp', 'has_attachment']
    list_filter = ['room', 'timestamp', 'is_edited']
    search_fields = ['content', 'author__username', 'room__name']
    readonly_fields = ['id', 'timestamp', 'is_edited', 'edited_at']
    ordering = ['-timestamp']
    raw_id_fields = ['author', 'room']

    actions = ['delete_selected']

    def truncated_content(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content
    truncated_content.short_description = "Content"

    def has_attachment(self, obj):
        return bool(obj.file_attachment)
    has_attachment.boolean = True
    has_attachment.short_description = "Attachment"

    def has_add_permission(self, request):
        return False  # No manual creation

    def has_change_permission(self, request, obj=None):
        return False  # No editing


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'emoji', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    raw_id_fields = ['message', 'user']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'last_activity', 'is_online', 'is_typing', 'typing_in_room']
    list_filter = ['is_online', 'is_typing', 'last_activity']
    search_fields = ['user__username']
    readonly_fields = ['last_activity']
    ordering = ['-last_activity']
    raw_id_fields = ['user', 'typing_in_room']

    actions = ['clear_all_activity']

    def clear_all_activity(self, request, queryset):
        """Clear all user activity data"""
        if not has_chat_admin_permission(request.user):
            messages.error(request, "Only super administrators can perform this action.")
            return

        count = queryset.count()
        queryset.delete()
        messages.success(request, f"Cleared activity data for {count} users.")

    clear_all_activity.short_description = "Clear selected user activity"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return has_chat_admin_permission(request.user)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'email_notifications', 'push_notifications', 'sound_enabled']
    list_filter = ['notification_type', 'email_notifications', 'push_notifications', 'sound_enabled']
    search_fields = ['user__username']
    raw_id_fields = ['user']

    actions = ['reset_to_defaults']

    def reset_to_defaults(self, request, queryset):
        """Reset preferences to defaults (all enabled, all messages)"""
        if not has_chat_admin_permission(request.user):
            messages.error(request, "Only super administrators can perform this action.")
            return

        count = queryset.update(
            notification_type='all',
            email_notifications=True,
            push_notifications=True,
            sound_enabled=True
        )
        messages.success(request, f"Reset {count} user preferences to defaults.")

    reset_to_defaults.short_description = "Reset to default preferences"

    def has_add_permission(self, request):
        return request.user.is_staff


# Custom admin view for chat system management
class ChatSystemAdmin(admin.ModelAdmin):
    """Special admin interface for system-wide chat operations"""

    def chat_management_view(self, request):
        """Super admin interface for chat system management"""
        if not has_chat_admin_permission(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Only super administrators can access this page.")

        from django.shortcuts import render
        from django.template.response import TemplateResponse

        # Handle form submissions
        if request.method == 'POST':
            action = request.POST.get('clear_action')
            if action:
                return self.handle_clear_action(request, action)

        # Get statistics
        context = {
            'total_rooms': ChatRoom.objects.count(),
            'total_messages': Message.objects.count(),
            'total_users_with_activity': UserActivity.objects.count(),
            'total_reactions': MessageReaction.objects.count(),
            'messages_with_attachments': Message.objects.filter(file_attachment__isnull=False).count(),
            'total_attachments_size': self.get_total_attachments_size(),
            'title': 'Chat System Management',
            'opts': self.opts,
        }

        return TemplateResponse(request, 'chat/admin/chat_system_management.html', context)

    def handle_clear_action(self, request, action):
        """Handle the different clear actions from the management interface"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        try:
            with transaction.atomic():
                if action == 'all':
                    # Clear everything
                    self.clear_all_messages()
                    self.clear_all_attachments()
                    self.clear_all_activity()
                    self.clear_all_preferences()
                    messages.success(request, "Successfully cleared all chat data from the system.")

                elif action == 'messages':
                    # Clear messages only
                    self.clear_all_messages()
                    messages.success(request, "Successfully cleared all messages from all rooms.")

                elif action == 'attachments':
                    # Clear attachments only
                    self.clear_all_attachments()
                    messages.success(request, "Successfully cleared all file attachments.")

                elif action == 'activity':
                    # Clear activity only
                    self.clear_all_activity()
                    messages.success(request, "Successfully cleared all user activity data.")

        except Exception as e:
            messages.error(request, f"Error during clear operation: {str(e)}")

        return HttpResponseRedirect(reverse('admin:chat_system_management'))

    def clear_all_messages(self):
        """Clear all messages and related data"""
        messages = Message.objects.all()
        reaction_count = MessageReaction.objects.all().delete()[0]
        read_status_count = MessageReadStatus.objects.all().delete()[0]

        messages.delete()
        return {'reactions': reaction_count, 'read_statuses': read_status_count}

    def clear_all_attachments(self):
        """Clear all file attachments"""
        deleted_count = 0
        attachment_dir = os.path.join(settings.MEDIA_ROOT, 'chat_attachments')

        messages_with_attachments = Message.objects.filter(file_attachment__isnull=False)
        for message in messages_with_attachments:
            if message.file_attachment and message.file_attachment.name:
                file_path = os.path.join(settings.MEDIA_ROOT, str(message.file_attachment))
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    pass  # Continue with other files

            # Clear file fields
            message.file_attachment = None
            message.file_name = None
            message.save()

        # Clean up empty directories
        if os.path.exists(attachment_dir) and not os.listdir(attachment_dir):
            try:
                os.rmdir(attachment_dir)
            except:
                pass

        return deleted_count

    def clear_all_activity(self):
        """Clear all user activity data"""
        return UserActivity.objects.all().delete()[0]

    def clear_all_preferences(self):
        """Clear all notification preferences"""
        return NotificationPreference.objects.all().delete()[0]

    def get_total_attachments_size(self):
        """Calculate total size of all chat attachments"""
        total_size = 0
        import os

        attachment_dir = os.path.join(settings.MEDIA_ROOT, 'chat_attachments')
        if os.path.exists(attachment_dir):
            for root, dirs, files in os.walk(attachment_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        return self.format_bytes(total_size)

    def format_bytes(self, bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"


# Create a dummy model for the chat system admin to register the URLs
from django.db import models

class ChatSystemModel(models.Model):
    class Meta:
        app_label = 'chat'
        db_table = None  # No actual table
        managed = False  # Don't create migrations
        verbose_name = 'Chat System Management'
        verbose_name_plural = 'Chat System Management'

# Register the admin with the dummy model to make URLs available
admin.site.register(ChatSystemModel, ChatSystemAdmin)

# Manually add the chat management URL to the admin site
def chat_management_view(request):
    csa = ChatSystemAdmin(ChatSystemModel, admin.site)
    return admin.site.admin_view(csa.chat_management_view)(request)

# Monkey patch admin.site to add the URL at the root level
original_get_urls = admin.site.get_urls

def get_urls_with_chat_management():
    urls = original_get_urls()
    from django.urls import path
    urls.insert(0, path('chat-management/', chat_management_view, name='chat_system_management'))
    return urls

admin.site.get_urls = get_urls_with_chat_management
