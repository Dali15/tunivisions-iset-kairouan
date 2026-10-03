from django.test import TestCase
from django.urls import reverse
from accounts.models import User


class MemberProfileAccessTests(TestCase):
	def test_user_can_view_own_profile_without_member_list_permission(self):
		user = User.objects.create_user(username='self-profile', password='pass', role='active_member')
		self.client.force_login(user)
		self.assertEqual(self.client.get(reverse('member_profile', args=[user.pk])).status_code, 200)

	def test_direct_profile_url_requires_members_view_for_other_users(self):
		member = User.objects.create_user(username='profile-target', password='pass', role='active_member')
		denied = User.objects.create_user(username='profile-denied', password='pass', role='vp_mkc')
		self.client.force_login(denied)
		self.assertEqual(self.client.get(reverse('member_profile', args=[member.pk])).status_code, 403)

		allowed = User.objects.create_user(username='profile-allowed', password='pass', role='vp_rh')
		self.client.force_login(allowed)
		self.assertEqual(self.client.get(reverse('member_profile', args=[member.pk])).status_code, 200)


class MemberProfileManagementTests(TestCase):
	def setUp(self):
		self.target = User.objects.create_user(
			username='rh-profile-target',
			password='pass',
			role='active_member',
			bio='Avant',
			email='avant@example.test',
		)

	def test_vp_rh_can_edit_profile_without_changing_django_privileges(self):
		vp_rh = User.objects.create_user(username='rh-profile-manager', password='pass', role='vp_rh')
		self.client.force_login(vp_rh)

		response = self.client.post(
			reverse('manage_member_profile', args=[self.target.pk]),
			{
				'bio': 'Profil mis à jour',
				'first_name': 'Membre',
				'last_name': 'Modifié',
				'email': 'membre@example.test',
				'skills': 'Communication',
				'phone': '+216 00 000 000',
				'role': 'president',
				'is_staff': 'on',
				'is_superuser': 'on',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.target.refresh_from_db()
		self.assertEqual(self.target.bio, 'Profil mis à jour')
		self.assertEqual(self.target.first_name, 'Membre')
		self.assertEqual(self.target.last_name, 'Modifié')
		self.assertEqual(self.target.email, 'membre@example.test')
		self.assertEqual(self.target.skills, 'Communication')
		self.assertEqual(self.target.phone, '+216 00 000 000')
		self.assertEqual(self.target.role, 'active_member')
		self.assertFalse(self.target.is_staff)
		self.assertFalse(self.target.is_superuser)
		self.assertFalse(vp_rh.is_staff)
		self.assertFalse(vp_rh.is_superuser)

	def test_only_roles_with_members_manage_can_edit_profile(self):
		for role in ('assistant_rh', 'vp_mkc', 'vp_events', 'vp_bd', 'active_member'):
			with self.subTest(role=role):
				user = User.objects.create_user(
					username=f'rh-denied-{role}',
					password='pass',
					role=role,
				)
				self.client.force_login(user)
				response = self.client.post(
					reverse('manage_member_profile', args=[self.target.pk]),
					{'bio': f'Forbidden for {role}'},
				)
				self.assertEqual(response.status_code, 403)
				if role == 'assistant_rh':
					self.assertEqual(
						self.client.get(reverse('member_profile', args=[self.target.pk])).status_code,
						200,
					)

		self.target.refresh_from_db()
		self.assertEqual(self.target.bio, 'Avant')

	def test_rh_permissions_do_not_leak_to_business_development(self):
		vp_rh = User.objects.create_user(username='rh-no-bd', password='pass', role='vp_rh')
		assistant_rh = User.objects.create_user(
			username='assistant-rh-no-manage',
			password='pass',
			role='assistant_rh',
		)

		self.assertTrue(vp_rh.can_access('members.manage'))
		self.assertFalse(vp_rh.can_access('bd.view'))
		self.assertTrue(assistant_rh.can_access('members.view'))
		self.assertFalse(assistant_rh.can_access('members.manage'))
		self.assertFalse(assistant_rh.can_access('bd.view'))

	def test_staff_status_alone_does_not_grant_profile_management(self):
		staff = User.objects.create_user(
			username='rh-profile-staff-only',
			password='pass',
			role='active_member',
			is_staff=True,
		)
		self.client.force_login(staff)
		self.assertEqual(
			self.client.get(reverse('manage_member_profile', args=[self.target.pk])).status_code,
			403,
		)

	def test_anonymous_user_is_redirected_from_profile_management(self):
		response = self.client.get(reverse('manage_member_profile', args=[self.target.pk]))
		self.assertEqual(response.status_code, 302)
