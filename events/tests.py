from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from .models import Event, EventRegistration


class EventAccessTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username='event-owner', password='pass', role='president')
		self.member = User.objects.create_user(username='event-member', password='pass', role='active_member')
		self.denied = User.objects.create_user(username='event-denied', password='pass', role='vp_mkc')
		self.event = Event.objects.create(title='Event', description='Text', date=timezone.now(), location='Kairouan', created_by=self.owner)

	def test_event_detail_requires_events_view(self):
		self.client.force_login(self.member)
		self.assertEqual(self.client.get(reverse('event_detail', args=[self.event.pk])).status_code, 200)
		self.client.force_login(self.denied)
		self.assertEqual(self.client.get(reverse('event_detail', args=[self.event.pk])).status_code, 403)

	def test_register_event_is_post_only_and_requires_events_register(self):
		self.client.force_login(self.member)
		self.assertEqual(self.client.get(reverse('register_event', args=[self.event.pk])).status_code, 405)
		self.assertFalse(EventRegistration.objects.filter(user=self.member, event=self.event).exists())
		self.assertEqual(self.client.post(reverse('register_event', args=[self.event.pk])).status_code, 302)
		self.assertTrue(EventRegistration.objects.filter(user=self.member, event=self.event).exists())

		self.client.force_login(self.denied)
		self.assertEqual(self.client.post(reverse('register_event', args=[self.event.pk])).status_code, 403)


class EventCreationTests(TestCase):
	def test_authorized_events_role_can_create_event_with_post(self):
		organizer = User.objects.create_user(username='event-creator', password='pass', role='vp_events')
		self.client.force_login(organizer)
		url = reverse('create_event')
		self.assertEqual(self.client.get(url).status_code, 200)
		self.assertEqual(Event.objects.count(), 0)

		response = self.client.post(
			url,
			{
				'title': 'Événement créé',
				'description': 'Description',
				'date': '2030-10-21T15:30',
				'location': 'Kairouan',
				'max_attendees': '',
			},
		)
		self.assertEqual(response.status_code, 302)
		event = Event.objects.get(title='Événement créé')
		self.assertEqual(Event.objects.count(), 1)
		self.assertEqual(event.created_by, organizer)
		self.assertEqual(event.location, 'Kairouan')

	def test_event_creation_denies_roles_without_permission(self):
		for role in ('active_member', 'vp_rh', 'vp_mkc', 'vp_bd'):
			with self.subTest(role=role):
				user = User.objects.create_user(
					username=f'event-denied-create-{role}',
					password='pass',
					role=role,
				)
				self.client.force_login(user)
				response = self.client.post(
					reverse('create_event'),
					{
						'title': f'Interdit {role}',
						'description': 'Description',
						'date': '2030-10-21T15:30',
						'location': 'Kairouan',
					},
				)
				self.assertEqual(response.status_code, 403)
		self.assertEqual(Event.objects.filter(title__startswith='Interdit').count(), 0)
