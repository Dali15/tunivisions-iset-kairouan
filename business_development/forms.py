from django import forms
from .models import Interaction, Opportunity, Partner, Prospect


class TunivisionsModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            else:
                css_class = 'form-control'
            field.widget.attrs['class'] = css_class


class PartnerForm(TunivisionsModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False

    def clean_status(self):
        return self.cleaned_data.get('status') or Partner._meta.get_field('status').get_default()

    class Meta:
        model = Partner
        fields = '__all__'


class ProspectForm(TunivisionsModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
        self.fields['priority'].required = False

    def clean_status(self):
        return self.cleaned_data.get('status') or Prospect._meta.get_field('status').get_default()

    def clean_priority(self):
        return self.cleaned_data.get('priority') or Prospect._meta.get_field('priority').get_default()

    class Meta:
        model = Prospect
        fields = '__all__'


class OpportunityForm(TunivisionsModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False

    def clean_status(self):
        return self.cleaned_data.get('status') or Opportunity._meta.get_field('status').get_default()

    class Meta:
        model = Opportunity
        exclude = ('owner',)


class InteractionForm(TunivisionsModelForm):
    class Meta:
        model = Interaction
        exclude = ('owner',)
