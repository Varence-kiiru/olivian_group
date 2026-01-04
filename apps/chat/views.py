from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Q, Count, Max
from django.utils import timezone
from datetime import datetime, timedelta

from .models import ChatRoom, Message, MessageReadStatus, NotificationPreference, UserActivity, MessageReaction
from .forms import ChatRoomForm, MessageForm, RoomInvitationForm


@login_required
def chat_dashboard(request):
    """Main chat dashboard showing available rooms and allowing navigation"""

    # Mark user as online
    UserActivity.mark_user_online(request.user)

    # Get available rooms based on user permissions
    user = request.user
    rooms = ChatRoom.objects.filter(is_active=True)

    # Filter rooms based on user access
    accessible_rooms = []

    for room in rooms:
        if room.room_type == 'private':
            if room.participants.filter(id=user.id).exists():
                accessible_rooms.append(room)
        elif room.room_type == 'department':
            # Check if user belongs to appropriate department groups
            if user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff:
                accessible_rooms.append(room)
        elif room.room_type == 'general':
            # General rooms are accessible to all authenticated users
            accessible_rooms.append(room)
        elif room.room_type == 'project':
            # Check project access
            if user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff:
                accessible_rooms.append(room)
        else:
            accessible_rooms.append(room)

    # Get recent activity for each room
    for room in accessible_rooms:
        last_message = Message.objects.filter(room=room).order_by('-timestamp').first()
        room.last_message = last_message
        room.unread_count = get_unread_count(user, room)

    # Get online users (exclude current user)
    online_users = UserActivity.get_online_users().exclude(user=user).select_related('user')
    online_users_list = [activity.user for activity in online_users]

    context = {
        'rooms': accessible_rooms,
        'online_users': online_users_list,
        'websocket_url': get_websocket_url(request),
        'form': ChatRoomForm(),
    }

    return render(request, 'chat/chat_dashboard.html', context)


@login_required
def chat_room(request, room_name):
    """Display specific chat room"""

    # Mark user as online
    UserActivity.mark_user_online(request.user)

    room = get_object_or_404(ChatRoom, name=room_name, is_active=True)

    # Check access permissions
    user = request.user
    can_access = False

    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
    elif room.room_type == 'general':
        # General rooms are accessible to all authenticated users
        can_access = True
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
    else:
        can_access = True

    if not can_access:
        if request.method == 'POST' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Access denied'})
        messages.error(request, "You don't have access to this chat room.")
        return redirect('chat:dashboard')

    # Handle AJAX message sending
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            content = request.POST.get('content', '').strip()
            file_attachment = request.FILES.get('file_attachment')

            # Validate that either content or file is provided
            if not content and not file_attachment:
                return JsonResponse({
                    'success': False,
                    'error': 'Either message content or a file attachment is required.'
                })

            # Additional validation for content if provided
            if content and len(content) > 1000:
                return JsonResponse({
                    'success': False,
                    'error': 'Message cannot exceed 1000 characters.'
                })

            # File validation
            if file_attachment:
                # Size check (10MB)
                if file_attachment.size > 10 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'error': 'File size cannot exceed 10MB.'
                    })

                # Type check
                allowed_types = [
                    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain',
                    'application/zip', 'application/x-rar-compressed'
                ]

                if file_attachment.content_type not in allowed_types:
                    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
                    if not any(file_attachment.name.lower().endswith(ext) for ext in allowed_extensions):
                        return JsonResponse({
                            'success': False,
                            'error': 'Unsupported file type. Allowed: Images, PDF, Word docs, Text files, ZIP archives.'
                        })

            # Create message
            message = Message.objects.create(
                room=room,
                author=user,
                content=content,
                file_attachment=file_attachment,
                file_name=file_attachment.name if file_attachment else None
            )

            # Mark as read for sender
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=user,
                defaults={'read_at': message.timestamp}
            )

            return JsonResponse({
                'success': True,
                'message_id': message.id
            })

        # Regular POST for form submission
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = room
            message.author = user
            message.file_name = message.file_attachment.name if message.file_attachment else None
            message.save()

            # Mark as read for sender
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=user,
                defaults={'read_at': message.timestamp}
            )

            return redirect('chat:room', room_name=room_name)
    else:
        form = MessageForm()

    # Get recent messages
    messages_qs = Message.objects.filter(
        room=room
    ).select_related('author').order_by('-timestamp')

    # Mark messages as read (apply filters before slicing)
    unread_messages = messages_qs.filter(
        ~Q(author=user),
    ).exclude(id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True))[:50]

    # Apply read status to unread messages
    for message in unread_messages:
        MessageReadStatus.objects.get_or_create(
            message=message,
            user=user,
            defaults={'read_at': message.timestamp}
        )

    # Get the recent messages for display (slice after filtering)
    messages_for_display = messages_qs[:50]
    messages_list = list(reversed(messages_for_display))

    # Get online users in this room (include all users who have access and are online, including current user)
    online_activities = UserActivity.get_online_users().select_related('user')

    # For private rooms, only show participants; for other rooms, show all online users who have access
    if room.room_type == 'private':
        online_users = [activity.user for activity in online_activities if room.participants.filter(id=activity.user.id).exists()]
    elif room.room_type == 'department':
        online_users = [activity.user for activity in online_activities if user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff or activity.user.id == user.id]
    elif room.room_type == 'general':
        online_users = [activity.user for activity in online_activities]
    elif room.room_type == 'project':
        online_users = [activity.user for activity in online_activities if user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff or activity.user.id == user.id]
    else:
        online_users = [activity.user for activity in online_activities]

    context = {
        'room': room,
        'messages': messages_list,
        'online_users': online_users,
        'form': form,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        message_data = []
        for msg in messages_list:
            message_data.append({
                'id': msg.id,
                'content': msg.content,
                'author': msg.author.username,
                'author_id': msg.author.id,
                'timestamp': msg.timestamp.isoformat(),
                'is_edited': msg.is_edited,
            })
        return JsonResponse({
            'success': True,
            'messages': message_data
        })

    return render(request, 'chat/chat_room.html', context)


@login_required
def create_room(request):
    """Create a new chat room"""

    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.save()

            # Add creator to private rooms
            if room.room_type == 'private':
                room.participants.add(request.user)

            messages.success(request, f"Chat room '{room.name}' created successfully.")
            return redirect('chat:room', room_name=room.name)
    else:
        form = ChatRoomForm()

    context = {
        'form': form,
        'title': 'Create Chat Room',
    }

    return render(request, 'chat/room_form.html', context)


@login_required
def edit_room(request, room_name):
    """Edit chat room settings"""

    room = get_object_or_404(ChatRoom, name=room_name)

    # Check if user can edit (only creator or staff)
    if room.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this room.")
        return redirect('chat:room', room_name=room.name)

    if request.method == 'POST':
        form = ChatRoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"Chat room '{room.name}' updated successfully.")
            return redirect('chat:room', room_name=room.name)
    else:
        form = ChatRoomForm(instance=room)

    context = {
        'form': form,
        'room': room,
        'title': 'Edit Chat Room',
    }

    return render(request, 'chat/room_form.html', context)


@login_required
@require_POST
def delete_room(request, room_name):
    """Delete a chat room"""

    room = get_object_or_404(ChatRoom, name=room_name)

    # Check if user can delete (only creator or staff)
    if room.created_by != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    room.is_active = False
    room.save()

    messages.success(request, f"Chat room '{room.name}' has been deleted.")
    return redirect('chat:dashboard')


@login_required
def room_members(request, room_name):
    """Show room members"""

    room = get_object_or_404(ChatRoom, name=room_name, is_active=True)

    # Check access
    user = request.user
    can_access = False
    can_manage = False

    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
        can_manage = can_access  # Private room members can manage membership
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
        can_manage = user.is_staff  # Only staff can manage department room membership
    elif room.room_type == 'general':
        # General rooms are accessible to all authenticated users
        can_access = True
        can_manage = user.is_staff
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
        can_manage = user.groups.filter(name__in=['management', 'project-manager']).exists() or user.is_staff
    else:
        can_access = True
        can_manage = user.is_staff

    if not can_access:
        messages.error(request, "You don't have access to this room.")
        return redirect('chat:dashboard')

    # Handle member management for private and project rooms
    if request.method == 'POST' and can_manage:
        action = request.POST.get('action')

        if action == 'invite' and room.room_type in ['private', 'project']:
            form = RoomInvitationForm(request.POST, room=room)
            if form.is_valid():
                users_to_add = form.cleaned_data['usernames']
                for new_user in users_to_add:
                    room.participants.add(new_user)
                messages.success(request, f"Successfully added {len(users_to_add)} member(s) to {room.name}.")
                return redirect('chat:room_members', room_name=room.name)
            else:
                messages.error(request, "Error adding members. Please check the form and try again.")

        elif action == 'remove' and room.room_type in ['private', 'project']:
            user_id = request.POST.get('user_id')
            if user_id and user_id != str(user.id):  # Can't remove yourself
                try:
                    remove_user = User.objects.get(id=user_id)
                    if room.participants.filter(id=user_id).exists():
                        room.participants.remove(remove_user)
                        messages.success(request, f"Successfully removed {remove_user.get_display_name()} from {room.name}.")
                    else:
                        messages.error(request, "User is not a member of this room.")
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
            else:
                messages.error(request, "Cannot remove the specified user.")
            return redirect('chat:room_members', room_name=room_name)

    # Get members
    if room.room_type == 'private':
        members = room.participants.all()
    elif room.room_type == 'department':
        # For department rooms, show users who have access via groups
        group_names = [g.name for g in Group.objects.filter(name__icontains=room.name.lower())]
        members = []
        for group_name in group_names:
            group = Group.objects.filter(name=group_name).first()
            if group:
                members.extend(list(group.user_set.filter(is_active=True)))
        # Remove duplicates
        member_ids = set()
        unique_members = []
        for member in members:
            if member.id not in member_ids:
                unique_members.append(member)
                member_ids.add(member.id)
                # Add group info for display
                member.chat_groups = member.groups.filter(name__in=group_names)
        members = unique_members
    elif room.room_type == 'general':
        # General rooms are accessible to all authenticated users
        # Show all active users for general rooms
        members = User.objects.filter(is_active=True).order_by('username')
    else:
        members = []  # For project rooms
        if room.room_type == 'project':
            members = room.participants.all()

    invitation_form = None
    if can_manage and room.room_type in ['private', 'project']:
        invitation_form = RoomInvitationForm(room=room)

    context = {
        'room': room,
        'members': members,
        'can_manage': can_manage,
        'invitation_form': invitation_form,
    }

    return render(request, 'chat/room_members.html', context)


@login_required
def user_settings(request):
    """User chat preferences"""

    try:
        preferences = request.user.chat_preferences
    except NotificationPreference.DoesNotExist:
        preferences = None

    if request.method == 'POST':
        notification_type = request.POST.get('notification_type', 'all')
        email_notifications = request.POST.get('email_notifications') == 'on'
        push_notifications = request.POST.get('push_notifications') == 'on'
        sound_enabled = request.POST.get('sound_enabled') == 'on'

        if preferences:
            preferences.notification_type = notification_type
            preferences.email_notifications = email_notifications
            preferences.push_notifications = push_notifications
            preferences.sound_enabled = sound_enabled
            preferences.save()
        else:
            NotificationPreference.objects.create(
                user=request.user,
                notification_type=notification_type,
                email_notifications=email_notifications,
                push_notifications=push_notifications,
                sound_enabled=sound_enabled,
            )

        messages.success(request, "Chat preferences updated successfully.")

    context = {
        'preferences': preferences,
    }

    return render(request, 'chat/user_settings.html', context)


def get_unread_count(user, room):
    """Get count of unread messages in a room for a user"""

    return Message.objects.filter(
        room=room
    ).exclude(author=user).exclude(
        id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
    ).count()


def get_websocket_url(request):
    """Get WebSocket URL for current environment"""

    scheme = 'wss' if request.is_secure() else 'ws'
    host = request.get_host()

    return f"{scheme}://{host}"


# API endpoints for AJAX calls

@login_required
def api_send_message(request, room_name):
    """API endpoint to send messages via AJAX"""

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    room = get_object_or_404(ChatRoom, name=room_name, is_active=True)
    user = request.user

    # Check access permissions
    can_access = False
    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
    elif room.room_type == 'general':
        # General rooms are accessible to all authenticated users
        can_access = True
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
    else:
        can_access = True

    if not can_access:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Get message content and file
    content = request.POST.get('content', '').strip()
    file_attachment = request.FILES.get('file_attachment')

    # Validate that either content or file is provided
    if not content and not file_attachment:
        return JsonResponse({
            'success': False,
            'error': 'Either message content or a file attachment is required.'
        })

    # Additional validation for content if provided
    if content and len(content) > 1000:
        return JsonResponse({
            'success': False,
            'error': 'Message cannot exceed 1000 characters.'
        })

    # File validation
    if file_attachment:
        # Size check (10MB)
        if file_attachment.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File size cannot exceed 10MB.'
            })

        # Type check
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/zip', 'application/x-rar-compressed'
        ]

        if file_attachment.content_type not in allowed_types:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
            if not any(file_attachment.name.lower().endswith(ext) for ext in allowed_extensions):
                return JsonResponse({
                    'success': False,
                    'error': 'Unsupported file type. Allowed: Images, PDF, Word docs, Text files, ZIP archives.'
                })

    # Handle reply functionality
    reply_to_id = request.POST.get('reply_to')
    reply_to = None
    if reply_to_id:
        try:
            reply_to = Message.objects.get(id=reply_to_id, room=room)
        except Message.DoesNotExist:
            reply_to = None

    # Create message
    message = Message.objects.create(
        room=room,
        author=user,
        content=content,
        file_attachment=file_attachment,
        file_name=file_attachment.name if file_attachment else None,
        reply_to=reply_to
    )

    # Mark as read for sender
    MessageReadStatus.objects.get_or_create(
        message=message,
        user=user,
        defaults={'read_at': message.timestamp}
    )

    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'reply_to': reply_to.id if reply_to else None,
        'reply_to_author': reply_to.author.username if reply_to else None,
        'reply_to_content': reply_to.content[:100] + '...' if reply_to and len(reply_to.content) > 100 else reply_to.content if reply_to else None,
    })


@login_required
def api_room_messages(request, room_name):
    """API endpoint to get messages for a room (for AJAX polling and pagination)"""

    try:
        room = get_object_or_404(ChatRoom, name=room_name, is_active=True)
        user = request.user

        # Check access permissions
        can_access = False
        if room.room_type == 'private':
            can_access = room.participants.filter(id=user.id).exists()
        elif room.room_type == 'department':
            can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
        elif room.room_type == 'general':
            # General rooms are accessible to all authenticated users
            can_access = True
        elif room.room_type == 'project':
            can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
        else:
            can_access = True

        if not can_access:
            return JsonResponse({'success': False, 'error': 'Access denied'})

        # Get parameters
        last_id = request.GET.get('last_id')  # For polling new messages
        before_id = request.GET.get('before_id')  # For loading older messages
        limit_str = request.GET.get('limit', '50')
        limit = 50  # Default
        try:
            limit = min(int(limit_str), 100)  # Cap at 100 messages per request
        except (ValueError, TypeError):
            limit = 50

        # Base queryset - use prefetch_related and select_related for efficiency
        messages_qs = Message.objects.filter(room=room).select_related('author', 'reply_to', 'reply_to__author')

        if last_id:
            # Polling for new messages since last_id
            last_id_int = 0
            try:
                last_id_int = int(last_id)
            except (ValueError, TypeError):
                last_id_int = 0

            messages_qs = messages_qs.filter(id__gt=last_id_int).order_by('-timestamp')

            # Mark messages as read - only get messages that exist
            if messages_qs.exists():
                unread_messages = messages_qs.exclude(author=user)
                for message in unread_messages:
                    MessageReadStatus.objects.get_or_create(
                        message=message,
                        user=user,
                        defaults={'read_at': message.timestamp}
                    )

            # Get messages in chronological order
            messages_qs = messages_qs.order_by('timestamp')

        elif before_id:
            # Loading older messages before before_id
            before_id_int = 0
            try:
                before_id_int = int(before_id)
            except (ValueError, TypeError):
                before_id_int = 0

            # Get IDs of older messages first, then retrieve them in correct order
            older_message_ids = messages_qs.filter(
                id__lt=before_id_int
            ).order_by('-timestamp').values_list('id', flat=True)[:limit]

            # Convert to list to evaluate the query, then get full objects in chronological order
            message_ids_list = list(older_message_ids)
            if message_ids_list:
                messages_qs = Message.objects.filter(id__in=message_ids_list).select_related(
                    'author', 'reply_to', 'reply_to__author'
                ).order_by('timestamp')
            else:
                messages_qs = Message.objects.none()

        else:
            # Initial load - get most recent messages
            # Get IDs of recent messages first, then retrieve them in correct order
            recent_message_ids = messages_qs.order_by('-timestamp').values_list('id', flat=True)[:limit]

            # Convert to list to evaluate the query, then get full objects in chronological order
            message_ids_list = list(recent_message_ids)
            if message_ids_list:
                messages_qs = Message.objects.filter(id__in=message_ids_list).select_related(
                    'author', 'reply_to', 'reply_to__author'
                ).order_by('timestamp')

                # Mark recent messages as read
                recent_messages = Message.objects.filter(id__in=message_ids_list).exclude(author=user)
                for message in recent_messages:
                    MessageReadStatus.objects.get_or_create(
                        message=message,
                        user=user,
                        defaults={'read_at': message.timestamp}
                    )
            else:
                messages_qs = Message.objects.none()

        # Convert to list to avoid multiple evaluations
        try:
            messages_list = list(messages_qs)
        except Exception as e:
            # If queryset evaluation fails, return error
            return JsonResponse({
                'success': False,
                'error': f'Database query failed: {str(e)}'
            }, status=500)

        # Check if there are more messages available - safely
        total_messages = 0
        has_more = False
        try:
            total_messages = Message.objects.filter(room=room).count()

            if before_id and messages_list:
                # For pagination, check if there are older messages
                oldest_loaded_id = messages_list[0].id
                has_more = Message.objects.filter(room=room, id__lt=oldest_loaded_id).exists()
            elif not before_id and not last_id:
                # For initial load, check if total is greater than what we returned
                has_more = total_messages > len(messages_list)
        except Exception as e:
            # If count query fails, continue without has_more calculation
            has_more = False

        # Format message data with safe field access
        message_data = []
        for msg in messages_list:
            try:
                # Handle reply_to data safely
                reply_to_data = None
                if msg.reply_to:
                    reply_author_name = ""
                    try:
                        reply_author_name = msg.reply_to.author.get_full_name() or msg.reply_to.author.username
                    except (AttributeError, Exception):
                        reply_author_name = msg.reply_to.author.username if msg.reply_to.author else "Unknown"

                    reply_to_data = {
                        'id': msg.reply_to.id,
                        'content': (msg.reply_to.content[:100] + '...' if len(msg.reply_to.content) > 100 else msg.reply_to.content) if msg.reply_to.content else "",
                        'author': reply_author_name,
                        'author_id': msg.reply_to.author.id if msg.reply_to.author else None,
                    }

                # Safe author data access
                author_full_name = ""
                author_role = ""
                try:
                    author_full_name = msg.author.get_full_name() or msg.author.username
                    author_role = msg.author.get_role_display()
                except (AttributeError, Exception):
                    author_full_name = msg.author.username
                    author_role = "Unknown"

                message_data.append({
                    'id': msg.id,
                    'content': msg.content or "",
                    'author': msg.author.username,
                    'author_full_name': author_full_name,
                    'author_id': msg.author.id,
                    'author_role': author_role,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'is_edited': msg.is_edited,
                    'reply_to': reply_to_data,
                })
            except Exception as msg_error:
                # If a single message fails to serialize, skip it but continue with others
                print(f"Warning: Failed to serialize message {msg.id}: {str(msg_error)}")
                continue

        return JsonResponse({
            'success': True,
            'messages': message_data,
            'has_more': has_more,
            'total_messages': total_messages
        })

    except Exception as e:
        # Add detailed logging for debugging
        import traceback
        print(f"API Error in api_room_messages (room: {request.GET.get('room_name', 'unknown')}): {str(e)}")
        print(traceback.format_exc())

        # Return JSON error response
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }, status=500)


@login_required
def api_room_info(request, room_name):
    """API endpoint to get room information"""

    room = get_object_or_404(ChatRoom, name=room_name, is_active=True)

    data = {
        'name': room.name,
        'type': room.room_type,
        'description': room.description,
        'created_at': room.created_at.isoformat(),
        'participants_count': room.get_participants_count(),
    }

    return JsonResponse(data)


@login_required
def api_online_users(request):
    """API endpoint to get online users"""

    # Mark current user as online
    UserActivity.mark_user_online(request.user)

    # Get all online users (including current user for this endpoint)
    online_activities = UserActivity.get_online_users().select_related('user')
    online_users = []
    for activity in online_activities:
        online_users.append({
            'id': activity.user.id,
            'username': activity.user.username,
            'fullname': f"{activity.user.first_name} {activity.user.last_name}".strip() or activity.user.username,
            'last_activity': activity.last_activity.isoformat(),
        })

    return JsonResponse({
        'online_users': online_users,
        'count': len(online_users),
    })


@login_required
def api_unread_count(request):
    """API endpoint to get unread message count for the current user"""

    user = request.user

    # Get accessible rooms first, then filter messages
    accessible_room_ids = []
    rooms = ChatRoom.objects.filter(is_active=True)

    for room in rooms:
        can_access = False
        if room.room_type == 'private':
            can_access = room.participants.filter(id=user.id).exists()
        elif room.room_type == 'department':
            can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
        elif room.room_type == 'general':
            # General rooms are accessible to all authenticated users
            can_access = True
        elif room.room_type == 'project':
            can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
        else:
            can_access = True

        if can_access:
            accessible_room_ids.append(room.id)

    if not accessible_room_ids:
        return JsonResponse({'unread_count': 0})

    # Get unread count from accessible rooms
    count = Message.objects.filter(
        room_id__in=accessible_room_ids
    ).exclude(author=user).exclude(
        id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
    ).count()

    return JsonResponse({'unread_count': count})


@login_required
def api_messages_global(request):
    """API endpoint to get global message notifications for polling"""

    user = request.user
    last_id = request.GET.get('last_id')

    try:
        if last_id:
            last_id = int(last_id)
        else:
            # For initial load, start from 0 to get recent messages
            last_id = 0
    except (ValueError, TypeError):
        last_id = 0

    # Get accessible rooms first, then filter messages
    accessible_room_ids = []
    rooms = ChatRoom.objects.filter(is_active=True)

    for room in rooms:
        can_access = False
        if room.room_type == 'private':
            can_access = room.participants.filter(id=user.id).exists()
        elif room.room_type == 'department':
            can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
        elif room.room_type == 'general':
            # General rooms are accessible to all authenticated users
            can_access = True
        elif room.room_type == 'project':
            can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
        else:
            can_access = True

        if can_access:
            accessible_room_ids.append(room.id)

    if not accessible_room_ids:
        return JsonResponse({'messages': [], 'unread_count': 0})

    # Get new messages since last_id from accessible rooms
    messages = Message.objects.filter(
        id__gt=last_id,
        room_id__in=accessible_room_ids
    ).exclude(author=user).exclude(
        id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
    ).select_related(
        'author', 'room'
    ).order_by('-timestamp')[:20]  # Limit to prevent overload

    # Convert to chronological order for processing
    messages = list(reversed(messages))

    # Calculate unread count from accessible rooms
    unread_count = Message.objects.filter(
        room_id__in=accessible_room_ids
    ).exclude(author=user).exclude(
        id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
    ).count()

    message_data = []
    for msg in messages:
        message_data.append({
            'id': msg.id,
            'content': msg.content,
            'author_full_name': f"{msg.author.first_name} {msg.author.last_name}".strip() or msg.author.username,
            'timestamp': msg.timestamp.isoformat(),
            'room_name': msg.room.name,
            'room': {
                'name': msg.room.name,
                'display_name': msg.room.name.title(),
            }
        })

    return JsonResponse({
        'messages': message_data,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def api_toggle_reaction(request, message_id):
    """API endpoint to add or remove emoji reactions to messages"""

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found'})

    user = request.user
    emoji = request.POST.get('emoji')

    # Validate emoji
    if not emoji:
        return JsonResponse({'success': False, 'error': 'Emoji is required'})

    valid_emojis = [choice[0] for choice in MessageReaction.COMMON_EMOJIS]
    if emoji not in valid_emojis:
        return JsonResponse({'success': False, 'error': 'Invalid emoji'})

    # Check if user can access this message (room permissions)
    room = message.room
    can_access = False
    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
    elif room.room_type == 'general':
        can_access = True
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
    else:
        can_access = True

    if not can_access:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Check if reaction already exists
    existing_reaction = MessageReaction.objects.filter(
        message=message,
        user=user,
        emoji=emoji
    ).first()

    if existing_reaction:
        # Remove the reaction
        existing_reaction.delete()
        action = 'removed'
    else:
        # Add the reaction
        MessageReaction.objects.create(
            message=message,
            user=user,
            emoji=emoji
        )
        action = 'added'

    # Get updated reaction summary
    summary = MessageReaction.get_reaction_summary(message)

    # Prepare reaction data for frontend
    reactions_data = {}
    for emoji_key, data in summary.items():
        reactions_data[emoji_key] = {
            'count': data['count'],
            'users': [user.get_full_name() or user.username for user in data['users']],
            'has_reacted': user in data['users']
        }

    return JsonResponse({
        'success': True,
        'action': action,
        'emoji': emoji,
        'reactions': reactions_data
    })


@login_required
def api_message_reactions(request, message_id):
    """API endpoint to get reaction summary for a message"""

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found'})

    user = request.user

    # Check permissions
    room = message.room
    can_access = False
    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
    elif room.room_type == 'general':
        can_access = True
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
    else:
        can_access = True

    if not can_access:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Get reaction summary
    summary = MessageReaction.get_reaction_summary(message)

    # Prepare reaction data for frontend
    reactions_data = {}
    for emoji_key, data in summary.items():
        reactions_data[emoji_key] = {
            'count': data['count'],
            'users': [user.get_full_name() or user.username for user in data['users']],
            'has_reacted': user in data['users']
        }

    return JsonResponse({
        'success': True,
        'reactions': reactions_data
    })


@login_required
@require_POST
def api_start_typing(request, room_name):
    """API endpoint to mark user as typing in a room"""

    room = get_object_or_404(ChatRoom, name=room_name, is_active=True)
    user = request.user

    # Check access permissions
    can_access = False
    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
    elif room.room_type == 'general':
        can_access = True
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
    else:
        can_access = True

    if not can_access:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Update typing status
    activity, created = UserActivity.objects.get_or_create(
        user=user,
        defaults={
            'last_activity': timezone.now(),
            'is_online': True,
            'is_typing': True,
            'typing_in_room': room,
            'last_typing_update': timezone.now()
        }
    )

    if not created:
        activity.is_typing = True
        activity.typing_in_room = room
        activity.last_typing_update = timezone.now()
        activity.is_online = True  # Also mark as online
        activity.last_activity = timezone.now()
        activity.save()

    return JsonResponse({'success': True})


@login_required
@require_POST
def api_stop_typing(request):
    """API endpoint to mark user as stopped typing"""

    user = request.user

    # Update typing status
    try:
        activity = user.chat_activity
        activity.is_typing = False
        activity.typing_in_room = None
        activity.last_typing_update = timezone.now()
        activity.save()
    except UserActivity.DoesNotExist:
        # Create activity record if it doesn't exist
        UserActivity.objects.create(
            user=user,
            is_typing=False,
            last_typing_update=timezone.now()
        )

    return JsonResponse({'success': True})


@login_required
def api_get_typing_users(request, room_name):
    """API endpoint to get users currently typing in a room"""

    room = get_object_or_404(ChatRoom, name=room_name, is_active=True)
    user = request.user

    # Check access permissions
    can_access = False
    if room.room_type == 'private':
        can_access = room.participants.filter(id=user.id).exists()
    elif room.room_type == 'department':
        can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
    elif room.room_type == 'general':
        can_access = True
    elif room.room_type == 'project':
        can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
    else:
        can_access = True

    if not can_access:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Get users typing in this room (within last 3 seconds, exclude current user)
    three_seconds_ago = timezone.now() - timedelta(seconds=3)
    typing_users = UserActivity.objects.filter(
        is_typing=True,
        typing_in_room=room,
        last_typing_update__gte=three_seconds_ago
    ).exclude(user=user).select_related('user')

    typing_user_data = []
    for activity in typing_users:
        typing_user_data.append({
            'id': activity.user.id,
            'username': activity.user.username,
            'full_name': f"{activity.user.first_name} {activity.user.last_name}".strip() or activity.user.username,
        })

    return JsonResponse({
        'success': True,
        'typing_users': typing_user_data
    })


@login_required
def api_search_messages(request):
    """API endpoint to search messages across accessible rooms with advanced features"""

    try:
        user = request.user
        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('type', 'text')  # text, mentions, threads, files
        room_filter = request.GET.get('room', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        mentioned_user = request.GET.get('mentioned_user', '')  # Username of mentioned user
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))

        # Validate inputs
        if not query and search_type == 'text':
            return JsonResponse({'success': False, 'error': 'Search query is required'})

        if query and len(query) < 2 and search_type == 'text':
            return JsonResponse({'success': False, 'error': 'Search query must be at least 2 characters'})

        # Get accessible rooms for the user
        accessible_rooms = []
        rooms = ChatRoom.objects.filter(is_active=True)

        for room in rooms:
            can_access = False
            if room.room_type == 'private':
                can_access = room.participants.filter(id=user.id).exists()
            elif room.room_type == 'department':
                can_access = user.groups.filter(name__icontains=room.name.lower()).exists() or user.is_staff
            elif room.room_type == 'general':
                can_access = True
            elif room.room_type == 'project':
                can_access = user.groups.filter(name__in=['management', 'staff', room.name.lower()]).exists() or user.is_staff
            else:
                can_access = True

            if can_access:
                accessible_rooms.append(room)

        if not accessible_rooms:
            return JsonResponse({
                'success': True,
                'results': [],
                'total': 0,
                'has_more': False
            })

        # Base queryset
        accessible_room_ids = [room.id for room in accessible_rooms]

        if search_type == 'mentions':
            # Search for @mentions
            message_qs = Message.objects.filter(
                room_id__in=accessible_room_ids,
                mentioned_users__username__icontains=query if query else ''
            ).distinct()

        elif search_type == 'threads':
            # Search within message threads
            thread_root_qs = Message.objects.filter(
                room_id__in=accessible_room_ids,
                reply_to__isnull=True,  # Thread starters
                content__icontains=query
            )
            message_qs = Message.objects.filter(
                Q(id__in=thread_root_qs.values('id')) |  # Thread starters
                Q(reply_to__in=thread_root_qs.values('id'))  # Replies in those threads
            )

        elif search_type == 'files':
            # Search within file names and descriptions
            message_qs = Message.objects.filter(
                room_id__in=accessible_room_ids,
                file_attachment__isnull=False
            )

            if query:
                # Search in file names and content
                file_search_query = Q()
                query_terms = query.split()
                for term in query_terms:
                    file_search_query |= Q(file_name__icontains=term)
                    file_search_query |= Q(content__icontains=term)
                message_qs = message_qs.filter(file_search_query)

            message_qs = message_qs.distinct()

        else:  # search_type == 'text'
            # Standard text search
            search_query = Q()
            query_terms = query.split()
            for term in query_terms:
                search_query |= Q(content__icontains=term)

            message_qs = Message.objects.filter(search_query, room_id__in=accessible_room_ids)

        # Apply room filter
        if room_filter:
            message_qs = message_qs.filter(room__name=room_filter)

        # Apply specific mentioned user filter
        if mentioned_user and mentioned_user.strip():
            try:
                mentioned_user_obj = User.objects.get(username=mentioned_user.strip())
                message_qs = message_qs.filter(mentioned_users=mentioned_user_obj)
            except User.DoesNotExist:
                pass  # Ignore invalid usernames

        # Apply date filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                from_datetime = timezone.datetime.combine(from_date, timezone.datetime.min.time())
                message_qs = message_qs.filter(timestamp__gte=from_datetime)
            except ValueError:
                pass  # Invalid date format, ignore

        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                to_datetime = timezone.datetime.combine(to_date, timezone.datetime.max.time())
                message_qs = message_qs.filter(timestamp__lte=to_datetime)
            except ValueError:
                pass  # Invalid date format, ignore

        # Get total count
        total_results = message_qs.count()

        # Apply pagination
        offset = (page - 1) * limit
        message_qs = message_qs.select_related('author', 'room').prefetch_related('mentioned_users').order_by('-timestamp')[offset:offset + limit]

        # Format results
        results = []
        for message in message_qs:
            # Highlight search terms in content (for text search)
            highlighted_content = message.content
            query_terms = query.split() if query else []

            if search_type == 'text':
                for term in query_terms:
                    highlighted_content = highlighted_content.replace(
                        f'<mark>{term}</mark>',
                        f'<mark>{term}</mark>',  # Don't double-mark
                        -1
                    )
                    # Simple case-insensitive highlighting
                    import re
                    highlighted_content = re.sub(
                        rf'({re.escape(term)})',
                        r'<mark>\1</mark>',
                        highlighted_content,
                        flags=re.IGNORECASE
                    )
            elif search_type == 'files':
                # Highlight file name matches
                if message.file_name:
                    for term in query_terms:
                        highlighted_content = re.sub(
                            rf'({re.escape(term)})',
                            r'<mark>\1</mark>',
                            highlighted_content,
                            flags=re.IGNORECASE
                        )

            # Get mentioned users
            mentioned_usernames = []
            if hasattr(message, 'mentioned_users') and message.mentioned_users.exists():
                mentioned_usernames = [u.username for u in message.mentioned_users.all()]

            results.append({
                'id': message.id,
                'content': message.content,
                'content_highlighted': highlighted_content,
                'author': {
                    'id': message.author.id,
                    'username': message.author.username,
                    'full_name': f"{message.author.first_name} {message.author.last_name}".strip() or message.author.username
                },
                'room': {
                    'id': message.room.id,
                    'name': message.room.name,
                    'type': message.room.room_type,
                    'type_display': message.room.get_room_type_display()
                },
                'timestamp': message.timestamp.isoformat(),
                'timestamp_display': message.timestamp.strftime('%b %d, %Y %H:%M'),
                'is_edited': message.is_edited,
                'has_file': message.file_attachment is not None,
                'file_name': message.file_name or '',
                'mentioned_users': mentioned_usernames,
                'is_thread_starter': message.reply_to is None,
                'in_thread': message.reply_to is not None,
                'reply_count': message.replies.count()
            })

        return JsonResponse({
            'success': True,
            'query': query,
            'search_type': search_type,
            'results': results,
            'total': total_results,
            'page': page,
            'limit': limit,
            'has_more': len(results) == limit and (offset + len(results)) < total_results
        })

    except Exception as e:
        # Add detailed logging for debugging
        import traceback
        print(f"API Error in api_search_messages: {str(e)}")
        print(traceback.format_exc())

        # Return JSON error response
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred while searching messages',
            'details': str(e)
        }, status=500)
