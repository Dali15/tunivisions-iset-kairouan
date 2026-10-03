from django.core.management.base import BaseCommand
from assistant.models import FAQ


class Command(BaseCommand):
    help = 'Populate sample FAQs for the assistant'

    def handle(self, *args, **options):
        faqs = [
            {
                'question': 'Quand est le prochain événement?',
                'answer': '📅 Les événements sont programmés chaque mois. Consultez la page "Événements" pour voir la liste complète avec les dates, heures et lieux de tous les événements à venir.',
                'keywords': 'événement, prochain, quand, date, agenda, planning',
                'category': 'events'
            },
            {
                'question': 'Comment m\'inscrire à un événement?',
                'answer': '✅ Pour vous inscrire à un événement:\n1. Allez sur la page "Événements"\n2. Cliquez sur l\'événement qui vous intéresse\n3. Cliquez sur le bouton "S\'inscrire"\n4. Confirmez votre participation\n\nVous recevrez une confirmation par email!',
                'keywords': 'inscrire, inscription, participer, événement, s\'inscrire, enregistrement',
                'category': 'registration'
            },
            {
                'question': 'Qu\'est-ce que le club AI?',
                'answer': '🤖 Le club AI est une communauté d\'étudiants passionnés par l\'intelligence artificielle, le machine learning et l\'innovation technologique. Nous organisons des événements, des projets et des discussions pour approfondir nos connaissances.',
                'keywords': 'club, ai, intelligence artificielle, à propos, qu\'est-ce',
                'category': 'general'
            },
            {
                'question': 'Qui peut rejoindre le club?',
                'answer': '🎓 Tous les étudiants de l\'université peuvent rejoindre le club AI! Aucune expérience préalable en AI n\'est requise. Il suffit d\'avoir de la curiosité et de la passion pour l\'apprentissage.',
                'keywords': 'rejoindre, adhérer, membre, inscription, qui',
                'category': 'members'
            },
            {
                'question': 'Comment contactez les responsables?',
                'answer': '📧 Vous pouvez nous contacter de plusieurs façons:\n• Par email: contact@tunivisions-kairouan.tn\n• Via les réseaux sociaux du club\n• En visitant notre bureau pendant les heures de permanence\n\nLes responsables sont généralement disponibles pour répondre à vos questions!',
                'keywords': 'contact, email, responsable, directeur, adresse, téléphone',
                'category': 'general'
            },
            {
                'question': 'Y a-t-il des frais d\'adhésion?',
                'answer': '💰 L\'adhésion au club AI est GRATUITE! Nous croyons que l\'éducation et la passion pour la technologie ne devraient pas être limitées par les frais. Rejoignez-nous sans engagement financier.',
                'keywords': 'frais, coût, prix, gratuit, adhésion, paiement',
                'category': 'general'
            },
            {
                'question': 'Quels projets le club entreprend-il?',
                'answer': '🎯 Nos projets incluent:\n• Développement d\'applications AI\n• Hackathons et compétitions\n• Ateliers pratiques de machine learning\n• Recherche collaborative\n• Mentoring par des professionnels du domaine\n\nConsultez la page "Projets" pour plus de détails!',
                'keywords': 'projet, travail, faire, activité, développement, recherche',
                'category': 'projects'
            },
            {
                'question': 'Comment contribuer au club?',
                'answer': '🤝 Il y a plusieurs façons de contribuer:\n• Participer activement aux événements\n• Proposer de nouveaux projets\n• Aider à organiser des événements\n• Partager vos connaissances avec d\'autres membres\n• Inviter vos amis intéressés\n\nToutées les contributions sont valorisées!',
                'keywords': 'contribuer, aider, participation, volontaire, bénévole',
                'category': 'general'
            },
        ]
        
        created_count = 0
        for faq_data in faqs:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults={
                    'answer': faq_data['answer'],
                    'keywords': faq_data['keywords'],
                    'category': faq_data['category'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created: {faq.question}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} FAQs created successfully!'))
