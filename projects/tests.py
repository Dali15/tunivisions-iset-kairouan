from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Project


class ProjectAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='project-owner', password='pass', role='president')
        self.project = Project.objects.create(title='Projet public', description='Description', created_by=self.owner)

    def test_active_member_can_view_projects(self):
        user = User.objects.create_user(username='active-project', password='pass', role='active_member')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('project_detail', args=[self.project.pk])).status_code, 200)

    def test_unassigned_role_cannot_bypass_projects_by_url(self):
        user = User.objects.create_user(username='mkc-project', password='pass', role='vp_mkc')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('project_detail', args=[self.project.pk])).status_code, 403)

    def test_events_roles_can_view_projects(self):
        user = User.objects.create_user(username='events-project', password='pass', role='vp_events')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 200)