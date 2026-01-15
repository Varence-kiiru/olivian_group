from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings

from .models import ChatRoom
from django.utils.text import slugify
from .models import GroupSlug
from .models import Message, PushSubscription, NotificationPreference, RoomMute
from . import webpush as webpush_utils
from concurrent.futures import ThreadPoolExecutor
import json

User = get_user_model()


def _match_room_group(room_name, group_name):
    rn = (room_name or '').lower()
    gn = (group_name or '').lower()
    return rn in gn or gn in rn


@receiver(m2m_changed, sender=User.groups.through)
def user_groups_changed(sender, instance, action, pk_set, **kwargs):
    """Sync user's group membership with department chat room participants.

    When a user is added to a group that matches a department room name,
    add them to that room's participants. When removed, remove them.
    """
    if action not in ('post_add', 'post_remove'):
        return

    try:
        groups = Group.objects.filter(pk__in=pk_set)
    except Exception:
        groups = []

    dept_rooms = ChatRoom.objects.filter(room_type='department')

    for group in groups:
        for room in dept_rooms:
            try:
                if _match_room_group(room.name, group.name):
                    if action == 'post_add':
                        room.participants.add(instance)
                    elif action == 'post_remove':
                        # remove safely
                        if room.participants.filter(id=instance.id).exists():
                            room.participants.remove(instance)
            except Exception:
                # guard against unexpected errors
                continue


@receiver(post_save, sender=User)
def user_created_auto_join_rooms(sender, instance, created, **kwargs):
    """When a new user account is created, automatically add them to
    general chat rooms and to department rooms inferred from their groups.
    """
    if not created:
        return

    # Add to all general rooms (configurable via settings.CHAT_AUTO_JOIN_GENERAL_ROOMS)
    try:
        general_rooms = ChatRoom.objects.filter(room_type='general', is_auto_join=True)
        configured = getattr(settings, 'CHAT_AUTO_JOIN_GENERAL_ROOMS', None)

        if isinstance(configured, (list, tuple)) and configured:
            general_rooms = general_rooms.filter(name__in=configured)

        for room in general_rooms:
            try:
                room.participants.add(instance)
            except Exception:
                continue
    except Exception:
        pass


@receiver(post_save, sender=Group)
def ensure_group_slug(sender, instance, created, **kwargs):
    """Ensure a GroupSlug exists for every Group, using a unique normalized slug."""
    try:
        base = slugify(instance.name) or 'group'
        slug = base
        counter = 1
        while GroupSlug.objects.filter(slug=slug).exclude(group=instance).exists():
            slug = f"{base}-{counter}"
            counter += 1

        GroupSlug.objects.update_or_create(group=instance, defaults={'slug': slug})
    except Exception:
        pass

    # Also ensure department rooms reflect initial group assignments
    try:
        user_groups = instance.groups.all()
        dept_rooms = ChatRoom.objects.filter(room_type='department', is_auto_join=True)
        for group in user_groups:
            for room in dept_rooms:
                if _match_room_group(room.name, group.name):
                    try:
                        room.participants.add(instance)
                    except Exception:
                        continue
    except Exception:
        pass


@receiver(post_save, sender=Message)
def notify_message_push(sender, instance, created, **kwargs):
    """Send Web Push notifications for new messages respecting user preferences and mutes.

    This runs send tasks in a small thread pool to avoid blocking the request thread.
    """
    if not created:
        return

    try:
        room = instance.room
        sender_user = instance.author

        # Build recipient queryset depending on room type
        recipients = []
        if room.room_type == 'private':
            recipients = list(room.participants.exclude(id=sender_user.id).distinct())
        elif room.room_type == 'department':
            # users in groups that match the room slug
            from .utils import get_user_group_slugs
            room_slug = slugify(room.name)
            # Basic approach: all users who have a matching GroupSlug or group slug
            from django.contrib.auth.models import Group
            matched_groups = Group.objects.filter(name__icontains=room.name)
            recipients = list(get_user_model().objects.filter(groups__in=matched_groups).exclude(id=sender_user.id).distinct())
        elif room.room_type == 'general':
            from django.contrib.auth import get_user_model
            recipients = list(get_user_model().objects.filter(is_active=True).exclude(id=sender_user.id))
        elif room.room_type == 'project':
            # For simplicity, deliver to users in groups or staff
            from django.contrib.auth import get_user_model
            recipients = list(get_user_model().objects.filter(is_active=True).exclude(id=sender_user.id))
        else:
            from django.contrib.auth import get_user_model
            recipients = list(get_user_model().objects.filter(is_active=True).exclude(id=sender_user.id))

        # Prepare payload
        payload = {
            'title': f"New message in {room.name}",
            'body': instance.content[:200],
            'room': room.name,
            'author': sender_user.get_full_name() or sender_user.username,
            'message_id': instance.id,
        }

        # Thread pool to send notifications concurrently
        executor = ThreadPoolExecutor(max_workers=6)
        futures = []

        for user in recipients:
            try:
                # Check user notification preference
                pref = None
                try:
                    pref = user.chat_preferences
                except Exception:
                    pref = None

                # Skip if user disabled push notifications
                if pref and not getattr(pref, 'push_notifications', True):
                    continue

                # Skip if user muted this room
                if RoomMute.objects.filter(user=user, room=room).exists():
                    continue

                # Collect subscriptions
                subs = PushSubscription.objects.filter(user=user)
                for s in subs:
                    sub_info = {
                        'endpoint': s.endpoint,
                        'keys': {
                            'p256dh': s.p256dh or '',
                            'auth': s.auth or ''
                        }
                    }

                    # schedule send
                    futures.append(executor.submit(webpush_utils.send_web_push, sub_info, payload))
            except Exception:
                continue

        # Optionally, wait for futures to complete briefly
        # do not block long - just allow threads to start
        # executor.shutdown(wait=False)
    except Exception:
        # avoid raising from signal
        return
