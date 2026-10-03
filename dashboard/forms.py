from django import forms

from .models import BureauMessage, FooterSettings


class BureauMessageForm(forms.ModelForm):
    class Meta:
        model = BureauMessage
        fields = ('recipient_role', 'subject', 'message')
        widgets = {
            'recipient_role': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }


class FooterSettingsForm(forms.ModelForm):
    class Meta:
        model = FooterSettings
        fields = (
            'organization_name',
            'description',
            'quick_links_title',
            'events_link_label',
            'announcements_link_label',
            'contact_title',
            'contact_email',
            'copyright_text',
        )
        labels = {
            'organization_name': 'Nom affiché',
            'description': 'Présentation',
            'quick_links_title': 'Titre de la section des liens',
            'events_link_label': 'Libellé du lien vers les événements',
            'announcements_link_label': 'Libellé du lien vers les annonces',
            'contact_title': 'Titre de la section contact',
            'contact_email': 'Adresse e-mail de contact',
            'copyright_text': 'Texte de copyright',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
