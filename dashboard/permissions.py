from django.http import HttpResponseForbidden
from functools import wraps
from accounts.rbac import has_role_permission


def has_permission(user, permission):
    """Check if user has permission using Django's built-in system."""
    legacy_map = {
        'view_members': 'members.view', 'manage_members': 'members.manage',
        'create_event': 'events.create', 'edit_event': 'events.edit',
        'delete_event': 'events.delete', 'view_events': 'events.view',
        'create_announcement': 'announcements.create', 'edit_announcement': 'announcements.edit',
        'delete_announcement': 'announcements.delete', 'create_project': 'projects.create',
        'edit_project': 'projects.edit', 'delete_project': 'projects.delete',
    }
    return has_role_permission(user, legacy_map.get(permission, permission))


def require_permission(permission):
    """Decorator to require a specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                return HttpResponseForbidden("Access denied.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
