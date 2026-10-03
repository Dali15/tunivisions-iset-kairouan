from django.conf import settings
from django.db import models


class Partner(models.Model):
    STATUS_CHOICES = [('prospect', 'Prospect'), ('contacted', 'Contacté'), ('discussion', 'En discussion'), ('partner', 'Partenaire'), ('inactive', 'Inactif'), ('refused', 'Refusé')]
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    social_links = models.TextField(blank=True)
    primary_contact = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prospect')
    partnership_start = models.DateField(null=True, blank=True)
    partnership_end = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Prospect(models.Model):
    STATUS_CHOICES = [('new', 'Nouveau'), ('contacted', 'Contacté'), ('discussion', 'En discussion'), ('converted', 'Converti'), ('refused', 'Refusé')]
    PRIORITY_CHOICES = [('low', 'Basse'), ('normal', 'Normale'), ('high', 'Haute')]
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    sector = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    next_action = models.CharField(max_length=255, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Opportunity(models.Model):
    STATUS_CHOICES = [('new', 'Nouveau'), ('contact', 'Contact'), ('negotiation', 'Négociation'), ('won', 'Gagné'), ('lost', 'Perdu')]
    title = models.CharField(max_length=200)
    partner = models.ForeignKey(Partner, null=True, blank=True, on_delete=models.SET_NULL, related_name='opportunities')
    prospect = models.ForeignKey(Prospect, null=True, blank=True, on_delete=models.SET_NULL, related_name='opportunities')
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bd_opportunities')
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Interaction(models.Model):
    TYPE_CHOICES = [('call', 'Appel'), ('email', 'Email'), ('meeting', 'Réunion'), ('message', 'Message'), ('encounter', 'Rencontre')]
    partner = models.ForeignKey(Partner, null=True, blank=True, on_delete=models.CASCADE, related_name='interactions')
    prospect = models.ForeignKey(Prospect, null=True, blank=True, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateTimeField()
    person = models.CharField(max_length=160, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bd_interactions')
    summary = models.TextField()
    next_action = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_interaction_type_display()} - {self.person or self.partner or self.prospect}'
