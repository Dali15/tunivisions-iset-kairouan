from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib import admin
from django.test import RequestFactory
from .models import User
from .rbac import ROLE_LABELS, has_role_permission
from .admin import CustomUserAdmin
from dashboard.models import ActivityLog, BureauMessage


class RoleBasedAccessTests(TestCase):
	roles = tuple(ROLE_LABELS)

	def test_all_requested_roles_are_defined(self):
		defined_roles = {key for key, _ in User.ROLE_CHOICES}
		self.assertTrue(set(self.roles).issubset(defined_roles))

	def test_president_has_full_access(self):
		user = User.objects.create_user(username='president', password='pass', role='president')
		self.assertTrue(has_role_permission(user, 'bd.manage'))
		self.assertTrue(has_role_permission(user, 'history.view'))

	def test_each_canonical_role_can_open_dashboard(self):
		for index, role in enumerate(self.roles):
			with self.subTest(role=role):
				user = User.objects.create_user(username=f'role-{index}', password='pass', role=role)
				self.client.force_login(user)
				response = self.client.get(reverse('dashboard'))
				self.assertEqual(response.status_code, 200)

	def test_active_member_cannot_create_event(self):
		user = User.objects.create_user(username='member', password='pass', role='active_member')
		self.client.force_login(user)
		response = self.client.get(reverse('create_event'))
		self.assertEqual(response.status_code, 403)

	def test_bd_assistant_can_view_but_not_manage(self):
		user = User.objects.create_user(username='bd-assistant', password='pass', role='assistant_bd')
		self.assertTrue(has_role_permission(user, 'bd.view'))
		self.assertTrue(has_role_permission(user, 'bd.interact'))
		self.assertFalse(has_role_permission(user, 'bd.manage'))

	def test_quick_actions_follow_rbac(self):
		cases = [
			('president', ['Create Event', 'Approve Members', 'Create Announcement', 'Approve Announcements', 'Chat Personnel', 'View History'], []),
			('vp_rh', ['Approve Members', 'View Members', 'Chat Personnel', 'View Events', 'View Announcements'], ['Create Event']),
			('vp_mkc', ['Create Announcement', 'Approve Announcements', 'View Announcements', 'Chat Personnel'], ['View Events', 'Approve Members']),
			('vp_bd', ['Add Partner', 'Add Prospect', 'Create Opportunity', 'Add Interaction', 'View Events', 'View Announcements', 'Chat Personnel'], ['Approve Members']),
			('active_member', ['View Events', 'View Announcements', 'Chat Personnel'], ['Create Event', 'Add Partner']),
		]
		for index, (role, visible, hidden) in enumerate(cases):
			with self.subTest(role=role):
				user = User.objects.create_user(username=f'quick-{index}', password='pass', role=role)
				self.client.force_login(user)
				response = self.client.get(reverse('dashboard'))
				for action in visible:
					self.assertContains(response, action)
				for action in hidden:
					self.assertNotContains(response, action)

	def test_president_app_access_does_not_depend_on_staff_flags(self):
		user = User.objects.create_user(username='flagless-president', password='pass', role='president')
		User.objects.filter(pk=user.pk).update(is_staff=False, is_superuser=False)
		user.refresh_from_db()
		self.client.force_login(user)
		self.assertEqual(self.client.get(reverse('activity_history')).status_code, 200)
		self.assertEqual(self.client.get(reverse('manage_member_roles')).status_code, 200)

	def test_president_role_does_not_promote_and_superuser_keeps_admin_flags(self):
		president = User.objects.create_user(username='functional-president', password='pass', role='president')
		self.assertFalse(president.is_staff)
		self.assertFalse(president.is_superuser)

		superuser = User.objects.create_superuser(username='django-admin', email='admin@example.com', password='pass', role='active_member')
		superuser.save()
		superuser.refresh_from_db()
		self.assertTrue(superuser.is_staff)
		self.assertTrue(superuser.is_superuser)
		self.assertTrue(superuser.can_access('bd.manage'))
		self.assertTrue(has_role_permission(superuser, 'bureau.messages.view'))
		self.assertFalse(has_role_permission(superuser, 'members.roles.manage'))

	def test_logout_handles_authenticated_and_anonymous_users(self):
		user = User.objects.create_user(username='logout-user', password='pass', role='active_member')
		self.client.force_login(user)
		response = self.client.post(reverse('logout'))
		self.assertEqual(response.status_code, 302)
		self.assertTrue(ActivityLog.objects.filter(user=user, action='logout').exists())

		response = self.client.post(reverse('logout'))
		self.assertEqual(response.status_code, 302)

	def test_approve_member_get_does_not_mutate_and_post_is_rbac_protected(self):
		approver = User.objects.create_user(username='approver', password='pass', role='vp_rh')
		target = User.objects.create_user(username='pending-a', password='pass', role='active_member', is_active=False)
		self.client.force_login(approver)
		self.assertEqual(self.client.get(reverse('approve_member', args=[target.pk])).status_code, 405)
		target.refresh_from_db()
		self.assertFalse(target.is_active)
		self.assertEqual(self.client.post(reverse('approve_member', args=[target.pk])).status_code, 302)
		target.refresh_from_db()
		self.assertTrue(target.is_active)

		denied = User.objects.create_user(username='denied-approve', password='pass', role='vp_mkc')
		target.is_active = False
		target.save(update_fields=['is_active'])
		self.client.force_login(denied)
		self.assertEqual(self.client.post(reverse('approve_member', args=[target.pk])).status_code, 403)
		target.refresh_from_db()
		self.assertFalse(target.is_active)

	def test_reject_member_get_does_not_mutate_and_post_is_rbac_protected(self):
		approver = User.objects.create_user(username='rejector', password='pass', role='vp_rh')
		target = User.objects.create_user(username='pending-r', password='pass', role='active_member', is_active=False)
		self.client.force_login(approver)
		self.assertEqual(self.client.get(reverse('reject_member', args=[target.pk])).status_code, 405)
		self.assertTrue(User.objects.filter(pk=target.pk).exists())
		self.assertEqual(self.client.post(reverse('reject_member', args=[target.pk])).status_code, 302)
		self.assertFalse(User.objects.filter(pk=target.pk).exists())

		target = User.objects.create_user(username='pending-denied', password='pass', role='active_member', is_active=False)
		denied = User.objects.create_user(username='denied-reject', password='pass', role='vp_mkc')
		self.client.force_login(denied)
		self.assertEqual(self.client.post(reverse('reject_member', args=[target.pk])).status_code, 403)
		self.assertTrue(User.objects.filter(pk=target.pk).exists())

	def test_only_president_can_change_functional_role(self):
		president = User.objects.create_user(username='role-president', password='pass', role='president')
		target = User.objects.create_user(username='role-target', password='pass', role='active_member')
		User.objects.filter(pk=target.pk).update(is_staff=True)

		self.client.force_login(president)
		self.assertEqual(self.client.get(reverse('manage_member_roles')).status_code, 200)
		response = self.client.post(
			reverse('update_member_role', args=[target.pk]),
			{'role': 'vp_mkc'},
		)
		self.assertEqual(response.status_code, 302)
		target.refresh_from_db()
		self.assertEqual(target.role, 'vp_mkc')
		self.assertTrue(target.is_staff)
		self.assertFalse(target.is_superuser)
		self.assertTrue(
			ActivityLog.objects.filter(
				content_type='User',
				object_id=target.pk,
				new_value=ROLE_LABELS['vp_mkc'],
			).exists()
		)

	def test_non_president_roles_cannot_change_functional_role(self):
		target = User.objects.create_user(username='unchanged-target', password='pass', role='active_member')
		denied_roles = (
			'vp_rh', 'vp_mkc', 'vp_events', 'vp_bd', 'assistant_rh',
			'assistant_comm_mkg', 'assistant_event', 'assistant_bd', 'active_member',
		)
		for index, role in enumerate(denied_roles):
			with self.subTest(role=role):
				user = User.objects.create_user(username=f'role-denied-{index}', password='pass', role=role)
				self.client.force_login(user)
				response = self.client.post(
					reverse('update_member_role', args=[target.pk]),
					{'role': 'president'},
				)
				self.assertEqual(response.status_code, 403)
				target.refresh_from_db()
				self.assertEqual(target.role, 'active_member')

	def test_staff_flag_does_not_grant_role_management(self):
		staff_user = User.objects.create_user(
			username='staff-without-president-role',
			password='pass',
			role='active_member',
		)
		target = User.objects.create_user(username='staff-role-target', password='pass', role='active_member')
		User.objects.filter(pk=staff_user.pk).update(is_staff=True)
		self.client.force_login(staff_user)
		response = self.client.post(
			reverse('update_member_role', args=[target.pk]),
			{'role': 'vp_rh'},
		)
		self.assertEqual(response.status_code, 403)
		target.refresh_from_db()
		self.assertEqual(target.role, 'active_member')

	def test_anonymous_cannot_manage_roles_and_get_does_not_mutate(self):
		target = User.objects.create_user(username='get-role-target', password='pass', role='active_member')
		self.assertEqual(self.client.get(reverse('manage_member_roles')).status_code, 302)
		self.assertEqual(
			self.client.post(reverse('update_member_role', args=[target.pk]), {'role': 'vp_rh'}).status_code,
			302,
		)

		president = User.objects.create_user(username='get-role-president', password='pass', role='president')
		self.client.force_login(president)
		self.assertEqual(self.client.get(reverse('update_member_role', args=[target.pk])).status_code, 405)
		target.refresh_from_db()
		self.assertEqual(target.role, 'active_member')

	def test_superuser_functional_role_cannot_be_changed(self):
		president = User.objects.create_user(username='protect-president', password='pass', role='president')
		superuser = User.objects.create_superuser(
			username='protected-superuser',
			email='protected@example.com',
			password='pass',
			role='active_member',
		)
		self.client.force_login(president)
		response = self.client.post(
			reverse('update_member_role', args=[superuser.pk]),
			{'role': 'president'},
		)
		self.assertEqual(response.status_code, 302)
		superuser.refresh_from_db()
		self.assertEqual(superuser.role, 'active_member')
		self.assertTrue(superuser.is_staff)
		self.assertTrue(superuser.is_superuser)

	def test_django_admin_cannot_edit_functional_roles(self):
		president = User.objects.create_user(username='admin-test-president', password='pass', role='president')
		request = RequestFactory().get('/admin/')
		request.user = president
		user_admin = CustomUserAdmin(User, admin.site)
		readonly_fields = user_admin.get_readonly_fields(request)
		self.assertIn('role', readonly_fields)
		self.assertIn('secondary_role', readonly_fields)

	def test_active_member_can_send_only_to_allowed_functional_groups(self):
		member = User.objects.create_user(username='message-member', password='pass', role='active_member')
		self.client.force_login(member)
		response = self.client.post(
			reverse('contact_bureau'),
			{'recipient_role': 'hr', 'subject': 'Question RH', 'message': 'Bonjour le bureau.'},
		)
		self.assertEqual(response.status_code, 302)
		self.assertTrue(
			BureauMessage.objects.filter(
				sender=member,
				recipient_role='hr',
				subject='Question RH',
				message='Bonjour le bureau.',
			).exists()
		)

		response = self.client.post(
			reverse('contact_bureau'),
			{'recipient_role': 'arbitrary-user', 'subject': 'Non valide', 'message': 'Test'},
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(BureauMessage.objects.filter(sender=member).count(), 1)

	def test_member_messages_are_private_and_bureau_inbox_is_role_filtered(self):
		member_one = User.objects.create_user(username='sender-one', password='pass', role='active_member')
		member_two = User.objects.create_user(username='sender-two', password='pass', role='active_member')
		hr_user = User.objects.create_user(username='recipient-hr', password='pass', role='assistant_rh')
		hr_message = BureauMessage.objects.create(
			sender=member_one,
			recipient_role='hr',
			subject='HR confidential',
			message='Message RH',
		)
		mkc_message = BureauMessage.objects.create(
			sender=member_two,
			recipient_role='mkc',
			subject='MKC confidential',
			message='Message MKC',
		)

		self.client.force_login(member_two)
		self.assertEqual(self.client.get(reverse('bureau_messages')).status_code, 403)
		response = self.client.get(reverse('contact_bureau'))
		self.assertContains(response, 'MKC confidential')
		self.assertNotContains(response, 'HR confidential')

		self.client.force_login(hr_user)
		response = self.client.get(reverse('bureau_messages'))
		self.assertContains(response, 'HR confidential')
		self.assertNotContains(response, 'MKC confidential')
		self.assertEqual(
			self.client.get(reverse('mark_bureau_message_read', args=[hr_message.pk])).status_code,
			405,
		)
		hr_message.refresh_from_db()
		self.assertFalse(hr_message.is_read)
		self.assertEqual(
			self.client.post(reverse('mark_bureau_message_read', args=[mkc_message.pk])).status_code,
			404,
		)
		self.assertEqual(
			self.client.post(reverse('mark_bureau_message_read', args=[hr_message.pk])).status_code,
			302,
		)
		hr_message.refresh_from_db()
		self.assertTrue(hr_message.is_read)

	def test_president_can_see_all_bureau_messages(self):
		sender = User.objects.create_user(username='global-sender', password='pass', role='active_member')
		message = BureauMessage.objects.create(
			sender=sender,
			recipient_role='bd',
			subject='Global view',
			message='Visible to President',
		)
		president = User.objects.create_user(username='global-president', password='pass', role='president')
		self.client.force_login(president)
		response = self.client.get(reverse('bureau_messages'))
		self.assertContains(response, 'Global view')
		self.assertContains(response, message.message)

	def test_bureau_message_views_require_login_and_keep_csrf(self):
		self.assertEqual(self.client.get(reverse('contact_bureau')).status_code, 302)
		self.assertEqual(self.client.get(reverse('bureau_messages')).status_code, 302)

		member = User.objects.create_user(username='csrf-member', password='pass', role='active_member')
		csrf_client = Client(enforce_csrf_checks=True)
		csrf_client.force_login(member)
		response = csrf_client.post(
			reverse('contact_bureau'),
			{'recipient_role': 'general', 'subject': 'CSRF', 'message': 'CSRF test'},
		)
		self.assertEqual(response.status_code, 403)
		self.assertFalse(BureauMessage.objects.filter(sender=member).exists())

		csrf_client.get(reverse('contact_bureau'))
		csrf_token = csrf_client.cookies['csrftoken'].value
		response = csrf_client.post(
			reverse('contact_bureau'),
			{
				'csrfmiddlewaretoken': csrf_token,
				'recipient_role': 'general',
				'subject': 'CSRF ok',
				'message': 'Token submitted',
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertTrue(BureauMessage.objects.filter(sender=member, subject='CSRF ok').exists())
