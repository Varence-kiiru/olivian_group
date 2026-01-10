from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.chat.models import ChatRoom

User = get_user_model()


class ChatSignalsTest(TestCase):
    def setUp(self):
        # Create a general room and a department room
        self.general_room = ChatRoom.objects.create(name='general', room_type='general', is_auto_join=True)
        self.dept_room = ChatRoom.objects.create(name='sales', room_type='department', is_auto_join=True)

        # Ensure group exists
        self.sales_group, _ = Group.objects.get_or_create(name='sales')

    def test_new_user_auto_join_general_and_department(self):
        # Create user and assign department via groups
        user = User.objects.create_user(username='jane', password='test123')

        # Initially should have been added to general room
        self.assertTrue(self.general_room.participants.filter(id=user.id).exists())

        # Now add user to sales group and ensure dept auto-join works
        user.groups.add(self.sales_group)
        user.refresh_from_db()
        self.assertTrue(self.dept_room.participants.filter(id=user.id).exists())

    def test_respect_is_auto_join_flag(self):
        # Create a room that opts out
        optout_room = ChatRoom.objects.create(name='announcements', room_type='general', is_auto_join=False)
        user = User.objects.create_user(username='bob', password='test123')

        # User should not be in optout_room
        self.assertFalse(optout_room.participants.filter(id=user.id).exists())
