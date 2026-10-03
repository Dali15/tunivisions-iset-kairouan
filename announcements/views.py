from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Announcement
from .forms import AnnouncementForm

from django.contrib import messages
from django.shortcuts import get_object_or_404

import traceback
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from accounts.decorators import permission_required

import traceback
from django.http import HttpResponse

@login_required
def announcement_list(request):
    """Display list of announcements with search functionality."""
    try:
        # By default, show only approved announcements
        announcements = Announcement.objects.filter(is_approved=True)
        
        my_pending = None
        if request.user.is_authenticated:
            my_pending = Announcement.objects.filter(author=request.user, is_approved=False)
        
        announcements = announcements.order_by('-created_at')
        
        search_query = request.GET.get('search', '')
        if search_query:
            announcements = announcements.filter(
                Q(title__icontains=search_query) | 
                Q(content__icontains=search_query)
            )
        
        context = {
            'announcements': announcements,
            'search_query': search_query,
            'can_review': request.user.can_access('announcements.approve'),
            'my_pending': my_pending,
        }
        return render(request, 'announcements/announcement_list.html', context)
    except Exception:
        error_info = traceback.format_exc()
        return HttpResponse(f"<h1>Debug Error</h1><pre>{error_info}</pre>", status=500)

@login_required
@permission_required('announcements.create')
@require_http_methods(['GET', 'POST'])
def create_announcement(request):
    """
    Create a new announcement. 
    - Owner/President: Auto-approved.
    - Others: Status = Pending.
    """
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            
            # Auto-approve for Top Admins
            if request.user.can_access('announcements.approve'):
                announcement.is_approved = True
                message = "Announcement published successfully!"
            else:
                announcement.is_approved = False
                message = "Announcement submitted for approval. The President will review it shortly."
            
            announcement.save()
            messages.success(request, message)
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()

    return render(request, 'announcements/create_announcement.html', {'form': form})

@login_required
def pending_announcements(request):
    """Interface for President to accept/reject announcements."""
    if not request.user.can_access('announcements.approve'):
        messages.error(request, "Access denied.")
        return redirect('announcement_list')
        
    pending = Announcement.objects.filter(is_approved=False).order_by('created_at')
    
    return render(request, 'announcements/pending_announcements.html', {'pending_announcements': pending})

@login_required
@permission_required('announcements.approve')
@require_POST
def approve_announcement(request, pk):
    """Approve execution."""
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_approved = True
    announcement.save()
    messages.success(request, f"Announcement '{announcement.title}' approved.")
    return redirect('pending_announcements')

@login_required
@permission_required('announcements.approve')
@require_POST
def reject_announcement(request, pk):
    """Reject execution."""
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.delete() # Or set status='rejected' if we had a status field. For now delete.
    messages.success(request, f"Announcement '{announcement.title}' rejected (deleted).")
    return redirect('pending_announcements')
