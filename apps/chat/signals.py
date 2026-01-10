from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings

from .models import ChatRoom

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
