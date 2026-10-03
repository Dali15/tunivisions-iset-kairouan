from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from .models import Interaction, Opportunity, Partner, Prospect


class BusinessDevelopmentAccessTests(TestCase):
    def test_bd_dashboard_is_restricted_to_bd_roles(self):
        user = User.objects.create_user(username='member', password='pass', role='active_member')
        self.client.force_login(user)
        response = self.client.get(reverse('business_development:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_bd_dashboard_is_available_to_vp_bd(self):
        user = User.objects.create_user(username='vp-bd', password='pass', role='vp_bd')
        Partner.objects.create(name='Tunivisions Partner')
        self.client.force_login(user)
        response = self.client.get(reverse('business_development:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Business Development')

    def test_vp_bd_can_create_edit_and_delete_partner(self):
        user = User.objects.create_user(username='vp-crud', password='pass', role='vp_bd')
        self.client.force_login(user)
        response = self.client.post(reverse('business_development:partner_create'), {'name': 'Premier partenaire'})
        self.assertEqual(response.status_code, 302)
        partner = Partner.objects.get()
        self.client.post(reverse('business_development:partner_edit', args=[partner.pk]), {'name': 'Partenaire mis à jour'})
        partner.refresh_from_db()
        self.assertEqual(partner.name, 'Partenaire mis à jour')
        response = self.client.post(reverse('business_development:partner_delete', args=[partner.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Partner.objects.filter(pk=partner.pk).exists())

    def test_assistant_bd_cannot_delete_partner(self):
        user = User.objects.create_user(username='assistant-crud', password='pass', role='assistant_bd')
        partner = Partner.objects.create(name='Protected partner')
        self.client.force_login(user)
        response = self.client.post(reverse('business_development:partner_delete', args=[partner.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Partner.objects.filter(pk=partner.pk).exists())

    def test_vp_bd_can_create_edit_and_delete_prospect_with_default_priority(self):
        user = User.objects.create_user(username='vp-prospect', password='pass', role='vp_bd')
        self.client.force_login(user)
        response = self.client.post(reverse('business_development:prospect_create'), {'name': 'Prospect A'})
        self.assertEqual(response.status_code, 302)
        prospect = Prospect.objects.get()
        self.assertEqual(prospect.priority, 'normal')
        self.client.post(reverse('business_development:prospect_edit', args=[prospect.pk]), {'name': 'Prospect B', 'priority': 'high'})
        prospect.refresh_from_db()
        self.assertEqual(prospect.name, 'Prospect B')
        self.assertEqual(prospect.priority, 'high')
        response = self.client.post(reverse('business_development:prospect_delete', args=[prospect.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Prospect.objects.filter(pk=prospect.pk).exists())

    def test_vp_bd_can_create_edit_and_delete_opportunity(self):
        user = User.objects.create_user(username='vp-opportunity', password='pass', role='vp_bd')
        self.client.force_login(user)
        response = self.client.post(reverse('business_development:opportunity_create'), {'title': 'Opportunity A'})
        self.assertEqual(response.status_code, 302)
        opportunity = Opportunity.objects.get()
        self.assertEqual(opportunity.owner, user)
        self.client.post(reverse('business_development:opportunity_edit', args=[opportunity.pk]), {'title': 'Opportunity B', 'status': 'negotiation'})
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.title, 'Opportunity B')
        self.assertEqual(opportunity.status, 'negotiation')
        response = self.client.post(reverse('business_development:opportunity_delete', args=[opportunity.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Opportunity.objects.filter(pk=opportunity.pk).exists())

    def test_vp_bd_can_create_edit_and_delete_interaction(self):
        user = User.objects.create_user(username='vp-interaction', password='pass', role='vp_bd')
        self.client.force_login(user)
        data = {'interaction_type': 'call', 'date': '2026-10-01 10:00', 'summary': 'Premier contact'}
        response = self.client.post(reverse('business_development:interaction_create'), data)
        self.assertEqual(response.status_code, 302)
        interaction = Interaction.objects.get()
        self.assertEqual(interaction.owner, user)
        self.client.post(reverse('business_development:interaction_edit', args=[interaction.pk]), {**data, 'summary': 'Contact mis à jour'})
        interaction.refresh_from_db()
        self.assertEqual(interaction.summary, 'Contact mis à jour')
        response = self.client.post(reverse('business_development:interaction_delete', args=[interaction.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Interaction.objects.filter(pk=interaction.pk).exists())

    def test_bd_deletes_require_post_and_active_member_has_no_admin_access(self):
        partner = Partner.objects.create(name='POST only')
        user = User.objects.create_user(username='active-bd', password='pass', role='active_member')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('business_development:partner_delete', args=[partner.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('business_development:dashboard')).status_code, 403)
        self.assertTrue(Partner.objects.filter(pk=partner.pk).exists())

    def test_assistant_bd_can_manage_interactions_but_not_bd_entities(self):
        user = User.objects.create_user(username='assistant-interaction', password='pass', role='assistant_bd')
        self.client.force_login(user)
        data = {'interaction_type': 'email', 'date': '2026-10-01 11:00', 'summary': 'Suivi'}
        self.assertEqual(self.client.post(reverse('business_development:interaction_create'), data).status_code, 302)
        self.assertEqual(self.client.get(reverse('business_development:partner_create')).status_code, 403)
        self.assertEqual(self.client.get(reverse('business_development:prospect_create')).status_code, 403)
        self.assertEqual(self.client.get(reverse('business_development:opportunity_create')).status_code, 403)

    def test_vp_bd_can_list_and_view_all_bd_details(self):
        user = User.objects.create_user(username='vp-details', password='pass', role='vp_bd')
        partner = Partner.objects.create(name='Partner detail')
        prospect = Prospect.objects.create(name='Prospect detail')
        opportunity = Opportunity.objects.create(title='Opportunity detail', owner=user)
        interaction = Interaction.objects.create(owner=user, interaction_type='call', date=timezone.now(), summary='Detail')
        self.client.force_login(user)
        routes = [
            ('partner_list', 'partner_detail', partner.pk),
            ('prospect_list', 'prospect_detail', prospect.pk),
            ('opportunity_list', 'opportunity_detail', opportunity.pk),
            ('interaction_list', 'interaction_detail', interaction.pk),
        ]
        for list_name, detail_name, pk in routes:
            with self.subTest(route=list_name):
                self.assertEqual(self.client.get(reverse(f'business_development:{list_name}')).status_code, 200)
                self.assertEqual(self.client.get(reverse(f'business_development:{detail_name}', args=[pk])).status_code, 200)

    def test_assistant_bd_can_consult_all_bd_details(self):
        user = User.objects.create_user(username='assistant-details', password='pass', role='assistant_bd')
        partner = Partner.objects.create(name='Assistant partner')
        prospect = Prospect.objects.create(name='Assistant prospect')
        opportunity = Opportunity.objects.create(title='Assistant opportunity', owner=user)
        interaction = Interaction.objects.create(owner=user, interaction_type='email', date=timezone.now(), summary='Assistant detail')
        self.client.force_login(user)
        for detail_name, pk in [('partner_detail', partner.pk), ('prospect_detail', prospect.pk), ('opportunity_detail', opportunity.pk), ('interaction_detail', interaction.pk)]:
            with self.subTest(route=detail_name):
                self.assertEqual(self.client.get(reverse(f'business_development:{detail_name}', args=[pk])).status_code, 200)

    def test_active_member_cannot_list_or_view_bd_details(self):
        user = User.objects.create_user(username='member-details', password='pass', role='active_member')
        partner = Partner.objects.create(name='Member blocked')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('business_development:partner_list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('business_development:partner_detail', args=[partner.pk])).status_code, 403)