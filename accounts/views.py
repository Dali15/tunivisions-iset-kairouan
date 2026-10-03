from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from .forms import CustomUserCreationForm
import os


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import User
from .rbac import has_any_role
from accounts.decorators import permission_required

def signup_view(request):
    """User registration/signup view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Special case: First user ever becomes Owner/Superuser automatically (active)
            User = get_user_model()
            if not User.objects.exists():
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True
                user.role = 'owner'
                user.save()
                login(request, user)
                messages.success(request, f'Welcome Owner {user.username}! Setup complete.')
                return redirect('dashboard')
            
            # Default behavior: Pending Approval
            user.is_active = False 
            user.save()
            
            messages.info(request, f'Account created for {user.username}! Please wait for an Admin to approve your account before you can log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def pending_members(request):
    """List members waiting for approval."""
    if not has_any_role(request.user, ['president', 'vp_rh', 'assistant_rh']):
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    # Pending members are those with is_active=False (but not if they were banned? Assuming inactive = pending for now)
    pending_users = User.objects.filter(is_active=False).order_by('-date_joined')
    
    return render(request, 'accounts/pending_members.html', {'pending_users': pending_users})

@login_required
@permission_required('members.approve')
@require_POST
def approve_member(request, user_id):
    """Approve a member."""
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f"User {user.username} approved successfully.")
    return redirect('pending_members')

@login_required
@permission_required('members.approve')
@require_POST
def reject_member(request, user_id):
    """Reject (delete) a member."""
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f"User {user.username} rejected (deleted).")
    return redirect('pending_members')
