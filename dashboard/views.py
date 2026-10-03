from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from events.models import Event, EventRegistration
from dashboard.models import ActivityLog, BureauMessage, FooterSettings
from dashboard.role_permissions import ROLE_PERMISSIONS, ALL_AVAILABLE_PERMISSIONS
from accounts.models import User as CustomUser
from accounts.rbac import (
    BUREAU_MESSAGE_RECIPIENT_ROLES,
    ROLE_LABELS,
    has_functional_role,
    has_role_permission,
    role_label,
)
from accounts.decorators import permission_required
from business_development.models import Interaction, Opportunity, Partner, Prospect
from announcements.models import Announcement
from .forms import BureauMessageForm, FooterSettingsForm


def home_view(request):
    """Display home page with statistics if user is authenticated."""
    context = {}
    
    if request.user.is_authenticated:
        context.update({
            'total_members': CustomUser.objects.filter(is_active=True).count(),
            'total_events': Event.objects.count(),
            'total_registrations': EventRegistration.objects.count(),
        })
    
    return render(request, 'home.html', context)


@login_required
def dashboard_view(request):
    """Display dashboard with statistics for authorized users."""
    role = request.user.role
    context = {'role': role, 'role_label': role_label(role)}

    # Show statistics for bureau members and admins
    if request.user.is_bureau():
        context.update({
            'total_members': CustomUser.objects.filter(is_active=True).count(),
            'total_events': Event.objects.count(),
            'total_registrations': EventRegistration.objects.count(),
        })

    if has_role_permission(request.user, 'events.view'):
        upcoming_events = Event.objects.filter(date__gte=timezone.now()).order_by('date')
        has_upcoming_events = upcoming_events.exists()
        if not has_upcoming_events:
            upcoming_events = Event.objects.order_by('-date')
        context['dashboard_events'] = upcoming_events[:5]
        context['event_section_title'] = (
            'Événements à venir' if has_upcoming_events else 'Événements récents'
        )

    if has_role_permission(request.user, 'announcements.view'):
        context['dashboard_announcements'] = Announcement.objects.filter(
            is_approved=True
        ).order_by('-created_at')[:5]

    context.update({
        'bd_stats': {
            'prospects': Prospect.objects.count(),
            'partners': Partner.objects.filter(status='partner').count(),
            'opportunities': Opportunity.objects.exclude(status__in=['won', 'lost']).count(),
            'interactions': Interaction.objects.count(),
        } if has_role_permission(request.user, 'bd.view') else None,
    })

    return render(request, 'dashboard/dashboard.html', context)


@login_required
@permission_required('members.roles.manage')
@require_http_methods(['GET', 'POST'])
def footer_settings_view(request):
    try:
        footer_settings = FooterSettings.objects.get(pk=1)
    except FooterSettings.DoesNotExist:
        footer_settings = FooterSettings(pk=1)
    if request.method == 'POST':
        form = FooterSettingsForm(request.POST, instance=footer_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Les informations du pied de page ont été enregistrées.')
            return redirect('footer_settings')
    else:
        form = FooterSettingsForm(instance=footer_settings)
    return render(request, 'dashboard/footer_settings.html', {'form': form})


@permission_required('history.view')
def activity_history_view(request):
    """Display full activity history - Admin only"""
    query = request.GET.get('q', '')
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    content_type_filter = request.GET.get('content_type', '')
    
    logs = ActivityLog.objects.all()
    
    # Search filter
    if query:
        logs = logs.filter(
            Q(object_name__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query)
        )
    
    # Action filter
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # User filter
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    # Content type filter
    if content_type_filter:
        logs = logs.filter(content_type=content_type_filter)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    actions = ActivityLog.ACTION_CHOICES
    users = logs.values_list('user', flat=True).distinct()
    content_types = logs.values_list('content_type', flat=True).distinct().order_by('content_type')
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'content_type_filter': content_type_filter,
        'actions': actions,
        'users': users,
        'content_types': content_types,
    }
    
    return render(request, 'dashboard/activity_history.html', context)


def is_owner_or_president(user):
    """Check if user is owner (superuser) or president"""
    return user.is_superuser or user.role == 'president'


@login_required
def manage_permissions_view(request):
    """Manage role permissions - Owner and President only"""
    
    # Check permissions
    if not is_owner_or_president(request.user):
        return redirect('dashboard')
    
    # Get all roles with their current permissions
    roles_data = []
    for role_key, role_info in ROLE_PERMISSIONS.items():
        roles_data.append({
            'key': role_key,
            'label': role_info['label'],
            'permissions': role_info['permissions'],
            'available_permissions': ALL_AVAILABLE_PERMISSIONS,
        })
    
    context = {
        'roles_data': roles_data,
        'all_permissions': ALL_AVAILABLE_PERMISSIONS,
        'user_is_admin': request.user.is_superuser,
    }
    
    return render(request, 'dashboard/manage_permissions.html', context)


@login_required
@require_http_methods(["POST"])
def update_role_permission_view(request):
    """Update permission for a specific role - Owner and President only"""
    
    # Check permissions
    if not is_owner_or_president(request.user):
        return JsonResponse({'success': False, 'message': 'Accès refusé'}, status=403)
    
    role = request.POST.get('role')
    permission = request.POST.get('permission')
    action = request.POST.get('action')  # 'add' or 'remove'
    
    if role not in ROLE_PERMISSIONS or not permission:
        return JsonResponse({'success': False, 'message': 'Données invalides'}, status=400)
    
    # Update the permission
    if action == 'add':
        if permission not in ROLE_PERMISSIONS[role]['permissions']:
            ROLE_PERMISSIONS[role]['permissions'].append(permission)
    elif action == 'remove':
        if permission in ROLE_PERMISSIONS[role]['permissions']:
            ROLE_PERMISSIONS[role]['permissions'].remove(permission)
    else:
        return JsonResponse({'success': False, 'message': 'Action invalide'}, status=400)
    
    # Log the change
    ActivityLog.objects.create(
        user=request.user,
        action='update',
        content_type='Permission',
        object_name=f"{role} - {permission}",
        new_value=f"{'Ajoutée' if action == 'add' else 'Supprimée'}: {permission}",
    )
    
    return JsonResponse({
        'success': True,
        'message': f"Permission {'ajoutée' if action == 'add' else 'supprimée'} avec succès",
        'permissions': ROLE_PERMISSIONS[role]['permissions'],
    })


@login_required
def view_role_permissions_view(request, role=None):
    """View permissions for a specific role"""
    
    if not role or role not in ROLE_PERMISSIONS:
        return redirect('manage_permissions')
    
    role_info = ROLE_PERMISSIONS[role]
    available_perms = [perm[0] for perm in ALL_AVAILABLE_PERMISSIONS]
    
    context = {
        'role': role,
        'role_label': role_info['label'],
        'permissions': role_info['permissions'],
        'available_permissions': ALL_AVAILABLE_PERMISSIONS,
        'is_owner_or_president': is_owner_or_president(request.user),
    }
    
    return render(request, 'dashboard/view_role_permissions.html', context)


@login_required
@permission_required('members.roles.manage')
def manage_member_roles_view(request):
    """List every account for the President's functional role management."""
    search_query = request.GET.get('search', '').strip()
    members = CustomUser.objects.all()
    if search_query:
        members = members.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    context = {
        'members': members.order_by('first_name', 'last_name', 'username'),
        'role_choices': ROLE_LABELS.items(),
        'search_query': search_query,
    }
    return render(request, 'admin/manage_member_roles.html', context)


@login_required
@permission_required('members.roles.manage')
@require_POST
def update_member_role_view(request, user_id):
    """Change only the functional role; Django staff flags remain untouched."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    new_role = request.POST.get('role', '')
    if target_user.is_superuser:
        messages.error(request, "Le rôle fonctionnel d'un superuser ne peut pas être modifié ici.")
    elif new_role not in ROLE_LABELS:
        messages.error(request, "Le rôle sélectionné est invalide.")
    else:
        old_role = target_user.role
        CustomUser.objects.filter(pk=target_user.pk).update(role=new_role)
        ActivityLog.objects.create(
            user=request.user,
            action='update',
            content_type='User',
            object_id=target_user.pk,
            object_name=target_user.get_full_name() or target_user.username,
            old_value=role_label(old_role),
            new_value=ROLE_LABELS[new_role],
        )
        messages.success(
            request,
            f"Le rôle de {target_user.get_full_name() or target_user.username} "
            f"a été modifié : {ROLE_LABELS[new_role]}.",
        )
    return redirect('manage_member_roles')


def _bureau_message_inbox(user):
    if has_role_permission(user, 'bureau.messages.view_all'):
        return BureauMessage.objects.select_related('sender').all()

    recipient_roles = []
    for key, (_, roles) in BUREAU_MESSAGE_RECIPIENT_ROLES.items():
        if has_functional_role(user, roles):
            recipient_roles.append(key)
    return BureauMessage.objects.select_related('sender').filter(
        recipient_role__in=recipient_roles
    )


@login_required
@permission_required('bureau.messages.send')
def contact_bureau_view(request):
    sent_messages = BureauMessage.objects.filter(sender=request.user)
    if request.method == 'POST':
        form = BureauMessageForm(request.POST)
        if form.is_valid():
            bureau_message = form.save(commit=False)
            bureau_message.sender = request.user
            bureau_message.save()
            messages.success(request, "Votre message a bien été envoyé au bureau.")
            return redirect('contact_bureau')
    else:
        form = BureauMessageForm()
    return render(
        request,
        'dashboard/contact_bureau.html',
        {'form': form, 'sent_messages': sent_messages},
    )


@login_required
@permission_required('bureau.messages.view')
def bureau_messages_view(request):
    return render(
        request,
        'dashboard/bureau_messages.html',
        {'bureau_messages': _bureau_message_inbox(request.user)},
    )


@login_required
@permission_required('bureau.messages.view')
@require_POST
def mark_bureau_message_read_view(request, message_id):
    bureau_message = get_object_or_404(
        _bureau_message_inbox(request.user),
        pk=message_id,
    )
    if not bureau_message.is_read:
        bureau_message.is_read = True
        bureau_message.save(update_fields=['is_read'])
    messages.success(request, "Le message a été marqué comme lu.")
    return redirect('bureau_messages')
