from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Event, EventRegistration
from accounts.decorators import permission_required, roles_required
from django.views.decorators.http import require_http_methods, require_POST
from .forms import EventForm


@login_required
@roles_required(['president', 'vp_events', 'assistant_event', 'vp_rh', 'assistant_rh', 'vp_bd', 'assistant_bd', 'active_member'])
def event_list(request):
    """Display list of events with search and filtering."""
    events = Event.objects.all().order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    event_type = request.GET.get('type', '')
    
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Get user's registrations for display
    user_registrations = EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True)
    
    context = {
        'events': events,
        'search_query': search_query,
        'event_type': event_type,
        'user_registrations': user_registrations,
        'event_types': Event.EVENT_TYPE_CHOICES,
    }
    return render(request, 'events/event_list.html', context)


@login_required
@permission_required('events.view')
def event_detail(request, event_id):
    """Display event detail with setup instructions."""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user is registered
    is_registered = EventRegistration.objects.filter(user=request.user, event=event).exists()
    
    # Get registrations count
    registrations_count = event.registrations.count()
    
    # Get attendees list (for organizer)
    attendees = None
    if request.user == event.created_by or request.user.can_access('events.edit'):
        attendees = event.registrations.select_related('user').order_by('-registered_at')
    
    context = {
        'event': event,
        'is_registered': is_registered,
        'registrations_count': registrations_count,
        'attendees': attendees,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
@permission_required('events.register')
@require_POST
def register_event(request, event_id):
    """Register user for an event."""
    event = get_object_or_404(Event, id=event_id)

    # Prevent double registration
    if not EventRegistration.objects.filter(user=request.user, event=event).exists():
        EventRegistration.objects.create(user=request.user, event=event)
        messages.success(request, f'You have successfully registered for {event.title}!')
    else:
        messages.info(request, 'You are already registered for this event.')

    return redirect('event_detail', event_id=event_id)


@login_required
@permission_required('events.create')
@require_http_methods(['GET', 'POST'])
def create_event(request):
    """Create a new event. Only Owner, President, VP, and Events Manager can create events."""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('event_detail', event_id=event.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})
