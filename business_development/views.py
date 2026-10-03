from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from accounts.decorators import permission_required
from .forms import InteractionForm, OpportunityForm, PartnerForm, ProspectForm
from .models import Interaction, Opportunity, Partner, Prospect


@login_required
@permission_required('bd.view')
def dashboard(request):
    context = {
        'prospects_count': Prospect.objects.exclude(status='refused').count(),
        'partners_count': Partner.objects.filter(status='partner').count(),
        'open_opportunities': Opportunity.objects.exclude(status__in=['won', 'lost']).count(),
        'won_opportunities': Opportunity.objects.filter(status='won').count(),
        'follow_ups': Prospect.objects.filter(follow_up_date__isnull=False).exclude(status__in=['converted', 'refused']).count(),
        'recent_interactions': Interaction.objects.select_related('owner', 'partner', 'prospect')[:8],
    }
    return render(request, 'business_development/dashboard.html', context)


@login_required
@permission_required('bd.view')
def partner_list(request):
    partners = Partner.objects.all()
    query = request.GET.get('q', '').strip()
    if query:
        partners = partners.filter(Q(name__icontains=query) | Q(sector__icontains=query) | Q(primary_contact__icontains=query))
    return render(request, 'business_development/list.html', {'title': 'Partenaires', 'items': partners, 'label_field': 'name', 'add_url': 'business_development:partner_create', 'detail_url': 'business_development:partner_detail', 'edit_url': 'business_development:partner_edit', 'delete_url': 'business_development:partner_delete', 'can_edit': request.user.can_access('bd.manage'), 'can_manage': request.user.can_access('bd.manage')})


@login_required
@permission_required('bd.view')
def prospect_list(request):
    prospects = Prospect.objects.all()
    return render(request, 'business_development/list.html', {'title': 'Prospects', 'items': prospects, 'label_field': 'name', 'add_url': 'business_development:prospect_create', 'detail_url': 'business_development:prospect_detail', 'edit_url': 'business_development:prospect_edit', 'delete_url': 'business_development:prospect_delete', 'can_edit': request.user.can_access('bd.manage'), 'can_manage': request.user.can_access('bd.manage')})


@login_required
@permission_required('bd.view')
def opportunity_list(request):
    opportunities = Opportunity.objects.select_related('owner', 'partner', 'prospect')
    return render(request, 'business_development/list.html', {'title': 'Opportunités', 'items': opportunities, 'label_field': 'title', 'add_url': 'business_development:opportunity_create', 'detail_url': 'business_development:opportunity_detail', 'edit_url': 'business_development:opportunity_edit', 'delete_url': 'business_development:opportunity_delete', 'can_edit': request.user.can_access('bd.manage'), 'can_manage': request.user.can_access('bd.manage')})


@login_required
@permission_required('bd.view')
def interaction_list(request):
    interactions = Interaction.objects.select_related('owner', 'partner', 'prospect')
    return render(request, 'business_development/list.html', {'title': 'Interactions', 'items': interactions, 'label_field': 'string', 'add_url': 'business_development:interaction_create', 'detail_url': 'business_development:interaction_detail', 'edit_url': 'business_development:interaction_edit', 'delete_url': 'business_development:interaction_delete', 'can_edit': request.user.can_access('bd.interact'), 'can_manage': request.user.can_access('bd.manage')})


def _detail_view(request, model, pk, title, fields):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.can_access('bd.view'):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Access denied.')
    obj = get_object_or_404(model, pk=pk)
    return render(request, 'business_development/detail.html', {
        'title': title,
        'object': obj,
        'fields': [(label, getattr(obj, name)) for label, name in fields],
    })


def partner_detail(request, pk):
    return _detail_view(request, Partner, pk, 'Partenaire', [('Nom', 'name'), ('Type', 'partner_type'), ('Secteur', 'sector'), ('Contact principal', 'primary_contact'), ('Statut', 'get_status_display')])


def prospect_detail(request, pk):
    return _detail_view(request, Prospect, pk, 'Prospect', [('Nom', 'name'), ('Contact', 'contact_person'), ('Secteur', 'sector'), ('Priorité', 'get_priority_display'), ('Statut', 'get_status_display')])


def opportunity_detail(request, pk):
    return _detail_view(request, Opportunity, pk, 'Opportunité', [('Titre', 'title'), ('Responsable', 'owner'), ('Statut', 'get_status_display'), ('Valeur estimée', 'estimated_value')])


def interaction_detail(request, pk):
    return _detail_view(request, Interaction, pk, 'Interaction', [('Type', 'get_interaction_type_display'), ('Personne', 'person'), ('Responsable', 'owner'), ('Résumé', 'summary')])


@require_http_methods(['GET', 'POST'])
def _form_view(request, form_class, template_title, permission='bd.manage', instance=None, success_url='business_development:dashboard', cancel_url='business_development:dashboard'):
    if not request.user.is_authenticated:
        return redirect('login')
    allowed = request.user.can_access(permission)
    if permission == 'bd.interact':
        allowed = allowed or request.user.can_access('bd.manage')
    if not allowed:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Access denied.')
    form = form_class(request.POST, instance=instance) if request.method == 'POST' else form_class(instance=instance)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if any(field.name == 'owner' for field in obj._meta.fields):
            obj.owner = request.user
        obj.save()
        messages.success(request, f'{template_title} enregistré.')
        return redirect(success_url)
    return render(
        request,
        'business_development/form.html',
        {'form': form, 'title': template_title, 'cancel_url': cancel_url},
    )


def partner_create(request):
    return _form_view(request, PartnerForm, 'Ajouter un partenariat', cancel_url='business_development:partner_list')


def partner_edit(request, pk):
    return _form_view(
        request,
        PartnerForm,
        'Modifier le partenariat',
        instance=get_object_or_404(Partner, pk=pk),
        cancel_url='business_development:partner_list',
    )


def prospect_create(request):
    return _form_view(request, ProspectForm, 'Ajouter un prospect', cancel_url='business_development:prospect_list')


def prospect_edit(request, pk):
    return _form_view(
        request,
        ProspectForm,
        'Modifier le prospect',
        instance=get_object_or_404(Prospect, pk=pk),
        cancel_url='business_development:prospect_list',
    )


def opportunity_create(request):
    return _form_view(request, OpportunityForm, 'Ajouter une opportunité', cancel_url='business_development:opportunity_list')


def opportunity_edit(request, pk):
    return _form_view(
        request,
        OpportunityForm,
        'Modifier l’opportunité',
        instance=get_object_or_404(Opportunity, pk=pk),
        cancel_url='business_development:opportunity_list',
    )


def interaction_create(request):
    return _form_view(request, InteractionForm, 'Ajouter une interaction', 'bd.interact', cancel_url='business_development:interaction_list')


def interaction_edit(request, pk):
    return _form_view(
        request,
        InteractionForm,
        'Modifier l’interaction',
        'bd.interact',
        instance=get_object_or_404(Interaction, pk=pk),
        cancel_url='business_development:interaction_list',
    )


def _delete_view(request, model, pk, label):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.can_access('bd.manage'):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Access denied.')
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    obj = get_object_or_404(model, pk=pk)
    obj.delete()
    messages.success(request, f'{label} supprimé.')
    return redirect('business_development:dashboard')


def partner_delete(request, pk):
    return _delete_view(request, Partner, pk, 'Partenaire')


def prospect_delete(request, pk):
    return _delete_view(request, Prospect, pk, 'Prospect')


def opportunity_delete(request, pk):
    return _delete_view(request, Opportunity, pk, 'Opportunité')


def interaction_delete(request, pk):
    return _delete_view(request, Interaction, pk, 'Interaction')
