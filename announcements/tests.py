from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from .models import Announcement


class AnnouncementMutationAccessTests(TestCase):
	def setUp(self):
		self.president = User.objects.create_user(username='announcement-president', password='pass', role='president')
		self.denied = User.objects.create_user(username='announcement-denied', password='pass', role='vp_events')

	def test_approve_announcement_is_post_only_and_permission_protected(self):
		announcement = Announcement.objects.create(title='Pending', content='Text', author=self.denied)
		self.client.force_login(self.president)
		self.assertEqual(self.client.get(reverse('approve_announcement', args=[announcement.pk])).status_code, 405)
		announcement.refresh_from_db()
		self.assertFalse(announcement.is_approved)
		self.assertEqual(self.client.post(reverse('approve_announcement', args=[announcement.pk])).status_code, 302)
		announcement.refresh_from_db()
		self.assertTrue(announcement.is_approved)

		denied_announcement = Announcement.objects.create(title='Denied', content='Text', author=self.denied)
		self.client.force_login(self.denied)
		self.assertEqual(self.client.post(reverse('approve_announcement', args=[denied_announcement.pk])).status_code, 403)
		self.assertFalse(Announcement.objects.get(pk=denied_announcement.pk).is_approved)

	def test_reject_announcement_is_post_only_and_permission_protected(self):
		announcement = Announcement.objects.create(title='Reject', content='Text', author=self.denied)
		self.client.force_login(self.president)
		self.assertEqual(self.client.get(reverse('reject_announcement', args=[announcement.pk])).status_code, 405)
		self.assertTrue(Announcement.objects.filter(pk=announcement.pk).exists())
		self.assertEqual(self.client.post(reverse('reject_announcement', args=[announcement.pk])).status_code, 302)
		self.assertFalse(Announcement.objects.filter(pk=announcement.pk).exists())

		denied_announcement = Announcement.objects.create(title='Denied reject', content='Text', author=self.denied)
		self.client.force_login(self.denied)
		self.assertEqual(self.client.post(reverse('reject_announcement', args=[denied_announcement.pk])).status_code, 403)
		self.assertTrue(Announcement.objects.filter(pk=denied_announcement.pk).exists())


class AnnouncementCreationTests(TestCase):
	def test_announcement_creation_uses_rbac_and_preserves_approval_workflow(self):
		mkc = User.objects.create_user(username='create-announcement-mkc', password='pass', role='vp_mkc')
		self.client.force_login(mkc)
		url = reverse('create_announcement')

		self.assertEqual(self.client.get(url).status_code, 200)
		self.assertEqual(Announcement.objects.count(), 0)
		response = self.client.post(url, {'title': 'Annonce validée', 'content': 'Contenu'})
		self.assertEqual(response.status_code, 302)
		announcement = Announcement.objects.get(title='Annonce validée')
		self.assertTrue(announcement.is_approved)
		self.assertEqual(announcement.author, mkc)

		assistant = User.objects.create_user(
			username='create-announcement-assistant',
			password='pass',
			role='assistant_comm_mkg',
		)
		self.client.force_login(assistant)
		response = self.client.post(url, {'title': 'Annonce à approuver', 'content': 'Contenu'})
		self.assertEqual(response.status_code, 302)
		self.assertFalse(Announcement.objects.get(title='Annonce à approuver').is_approved)

	def test_announcement_creation_denies_roles_without_permission(self):
		member = User.objects.create_user(username='create-announcement-member', password='pass', role='active_member')
		self.client.force_login(member)
		response = self.client.post(
			reverse('create_announcement'),
			{'title': 'Interdite', 'content': 'Contenu'},
		)
		self.assertEqual(response.status_code, 403)
		self.assertFalse(Announcement.objects.filter(title='Interdite').exists())

	def test_announcement_creation_requires_csrf(self):
		user = User.objects.create_user(username='create-announcement-csrf', password='pass', role='vp_mkc')
		client = self.client_class(enforce_csrf_checks=True)
		client.force_login(user)
		response = client.post(
			reverse('create_announcement'),
			{'title': 'Sans jeton CSRF', 'content': 'Contenu'},
		)
		self.assertEqual(response.status_code, 403)
		self.assertFalse(Announcement.objects.filter(title='Sans jeton CSRF').exists())
