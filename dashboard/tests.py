from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from announcements.models import Announcement
from events.models import Event
from members.models import Member
from dashboard.models import FooterSettings


class DashboardContentTests(TestCase):
    def setUp(self):
        self.president = User.objects.create_user(
            username='dashboard-president',
            password='pass',
            role='president',
        )
        self.client.force_login(self.president)

    def test_member_count_uses_active_accounts_instead_of_member_profiles(self):
        User.objects.create_user(username='dashboard-member-a', password='pass', role='active_member')
        User.objects.create_user(username='dashboard-member-b', password='pass', role='member')
        User.objects.create_superuser(
            username='dashboard-admin',
            email='dashboard-admin@example.com',
            password='pass',
            role='active_member',
        )
        User.objects.create_user(
            username='dashboard-inactive',
            password='pass',
            role='active_member',
            is_active=False,
        )
        self.assertEqual(Member.objects.count(), 0)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_members'], User.objects.filter(is_active=True).count())
        self.assertEqual(response.context['total_members'], 4)

        home_response = self.client.get(reverse('home'))
        self.assertEqual(home_response.context['total_members'], 4)

    def test_dashboard_lists_real_events_and_recent_approved_announcements(self):
        now = timezone.now()
        events = [
            Event.objects.create(
                title=title,
                description=f'{title} description',
                date=event_date,
                location=f'{title} venue',
                created_by=self.president,
            )
            for title, event_date in (
                ('Future event later', now + timedelta(days=4)),
                ('Future event soon', now + timedelta(days=1)),
                ('Past event', now - timedelta(days=1)),
            )
        ]
        older_announcement = Announcement.objects.create(
            title='Older published announcement',
            content='Older published content',
            author=self.president,
            is_approved=True,
        )
        newer_announcement = Announcement.objects.create(
            title='Newer published announcement',
            content='Newer published content',
            author=self.president,
            is_approved=True,
        )
        Announcement.objects.filter(pk=older_announcement.pk).update(
            created_at=now - timedelta(days=2)
        )
        Announcement.objects.filter(pk=newer_announcement.pk).update(
            created_at=now - timedelta(days=1)
        )
        Announcement.objects.create(
            title='Unapproved announcement',
            content='Not visible',
            author=self.president,
            is_approved=False,
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(
            [event.title for event in response.context['dashboard_events']],
            ['Future event soon', 'Future event later'],
        )
        self.assertEqual(
            [announcement.title for announcement in response.context['dashboard_announcements']],
            ['Newer published announcement', 'Older published announcement'],
        )
        self.assertContains(response, 'Future event soon')
        self.assertContains(response, reverse('event_detail', args=[events[1].pk]))
        self.assertContains(
            response,
            f'{reverse("announcement_list")}#announcement-{newer_announcement.pk}',
        )
        self.assertNotContains(response, 'Past event')
        self.assertNotContains(response, 'Unapproved announcement')

    def test_dashboard_sections_follow_existing_view_permissions(self):
        event = Event.objects.create(
            title='Restricted event card',
            description='Event content',
            date=timezone.now() + timedelta(days=1),
            location='Club',
            created_by=self.president,
        )
        announcement = Announcement.objects.create(
            title='Visible announcement card',
            content='Announcement content',
            author=self.president,
            is_approved=True,
        )
        mkc_vp = User.objects.create_user(
            username='dashboard-mkc-vp',
            password='pass',
            role='vp_mkc',
        )
        self.client.force_login(mkc_vp)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, announcement.title)
        self.assertNotContains(response, event.title)
        self.assertNotContains(response, reverse('event_detail', args=[event.pk]))
        self.assertNotContains(response, reverse('manage_member_roles'))


class FooterSettingsAccessTests(TestCase):
    def test_president_can_update_footer_without_django_staff_access(self):
        president = User.objects.create_user(
            username='footer-president',
            password='pass',
            role='president',
        )
        self.client.force_login(president)
        url = reverse('footer_settings')

        self.assertFalse(president.is_staff)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(FooterSettings.objects.filter(pk=1).exists())
        self.assertContains(self.client.get(reverse('dashboard')), reverse('footer_settings'))

        response = self.client.post(
            url,
            {
                'organization_name': 'Tunivisions Kairouan',
                'description': 'Présentation modifiée',
                'quick_links_title': 'Navigation',
                'events_link_label': 'Nos événements',
                'announcements_link_label': 'Actualités',
                'contact_title': 'Nous contacter',
                'contact_email': 'contact@example.test',
                'copyright_text': '© 2026 Tunivisions.',
            },
        )

        self.assertRedirects(response, url)
        settings = FooterSettings.objects.get(pk=1)
        self.assertEqual(settings.description, 'Présentation modifiée')
        self.assertEqual(settings.events_link_label, 'Nos événements')
        self.assertEqual(settings.contact_email, 'contact@example.test')
        self.assertContains(self.client.get(reverse('home')), 'Présentation modifiée')

    def test_non_president_cannot_access_footer_settings(self):
        for role in ('vp_rh', 'active_member'):
            with self.subTest(role=role):
                user = User.objects.create_user(
                    username=f'footer-denied-{role}',
                    password='pass',
                    role=role,
                )
                self.client.force_login(user)
                self.assertEqual(self.client.get(reverse('footer_settings')).status_code, 403)
                self.assertNotContains(self.client.get(reverse('dashboard')), reverse('footer_settings'))

    def test_anonymous_user_is_redirected_from_footer_settings(self):
        response = self.client.get(reverse('footer_settings'))
        self.assertEqual(response.status_code, 302)
