from django.db import models
from django.contrib.auth import get_user_model
from accounts.rbac import BUREAU_MESSAGE_RECIPIENT_ROLES

User = get_user_model()


class ActivityLog(models.Model):
    """Track all user activities and modifications"""
    
    ACTION_CHOICES = [
        ('create', '✨ Créé'),
        ('update', '✏️ Modifié'),
        ('delete', '🗑️ Supprimé'),
        ('view', '👁️ Consulté'),
        ('login', '🔓 Connexion'),
        ('logout', '🔒 Déconnexion'),
        ('register', '📝 Inscription'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.CharField(max_length=100, help_text="Type d'objet modifié (Event, User, etc.)")
    object_id = models.IntegerField(null=True, blank=True)
    object_name = models.CharField(max_length=255, help_text="Nom de l'objet modifié")
    old_value = models.TextField(blank=True, help_text="Ancienne valeur")
    new_value = models.TextField(blank=True, help_text="Nouvelle valeur")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Navigateur/Device")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['content_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = "Historique d'activité"
        verbose_name_plural = "Historiques d'activités"
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_name}"
    
    @property
    def time_ago(self):
        """Return human-readable time ago"""
        from django.utils.timezone import now
        diff = now() - self.timestamp
        
        if diff.days > 0:
            return f"Il y a {diff.days}j"
        elif diff.seconds > 3600:
            return f"Il y a {diff.seconds // 3600}h"
        elif diff.seconds > 60:
            return f"Il y a {diff.seconds // 60}m"
        else:
            return "À l'instant"


class BureauMessage(models.Model):
    RECIPIENT_CHOICES = tuple(
        (key, recipient[0])
        for key, recipient in BUREAU_MESSAGE_RECIPIENT_ROLES.items()
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bureau_messages_sent',
    )
    recipient_role = models.CharField(max_length=20, choices=RECIPIENT_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.get_recipient_role_display()})"


class FooterSettings(models.Model):
    organization_name = models.CharField(
        max_length=120,
        default='Tunivisions Kairouan',
        verbose_name='Nom affiché',
    )
    description = models.CharField(
        max_length=255,
        default='Plateforme officielle de coordination du club et de ses pôles.',
        verbose_name='Présentation',
    )
    quick_links_title = models.CharField(max_length=80, default='Liens rapides')
    events_link_label = models.CharField(max_length=80, default='Événements')
    announcements_link_label = models.CharField(max_length=80, default='Annonces')
    contact_title = models.CharField(max_length=80, default='Contact')
    contact_email = models.EmailField(max_length=254, default='med2006dali@gmail.com')
    copyright_text = models.CharField(
        max_length=160,
        default='© 2026 Tunivisions Kairouan. Tous droits réservés.',
    )

    class Meta:
        verbose_name = 'Configuration du pied de page'
        verbose_name_plural = 'Configuration du pied de page'

    def __str__(self):
        return self.organization_name
