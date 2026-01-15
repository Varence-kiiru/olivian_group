from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.chat.models import ChatRoom

User = get_user_model()


class ChatAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create(username='alice')
        self.user1.set_password('password')
        self.user1.save()

        self.user2 = User.objects.create(username='bob')
        self.user2.set_password('password')
        self.user2.save()

        # Create management group
        Group.objects.get_or_create(name='management')

    def test_department_access_by_slug(self):
        # Group name with spaces and different formatting
        grp, _ = Group.objects.get_or_create(name='Sales Dept')
        grp.user_set.add(self.user1)

        # Room name uses slug form
        room = ChatRoom.objects.create(name='sales-dept', room_type='department', created_by=self.user1)

        self.client.login(username='alice', password='password')
        url = reverse('chat:room', args=[room.name])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # user2 should be denied
        self.client.login(username='bob', password='password')
        resp2 = self.client.get(url)
        self.assertEqual(resp2.status_code, 302)  # redirected to dashboard

    def test_project_access_by_management(self):
        room = ChatRoom.objects.create(name='project-x', room_type='project', created_by=self.user1)

        # make user2 part of management group
        mgmt, _ = Group.objects.get_or_create(name='management')
        mgmt.user_set.add(self.user2)

        self.client.login(username='bob', password='password')
        url = reverse('chat:room', args=[room.name])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_project_access_by_group_slug(self):
        grp, _ = Group.objects.get_or_create(name='Project Alpha Team')
        grp.user_set.add(self.user1)
        room = ChatRoom.objects.create(name='project-alpha-team', room_type='project', created_by=self.user1)

        self.client.login(username='alice', password='password')
        url = reverse('chat:room', args=[room.name])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
