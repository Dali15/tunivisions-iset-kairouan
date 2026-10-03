from django.http import HttpResponseForbidden
from functools import wraps
from .rbac import has_any_role, has_role_permission

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if has_role_permission(request.user, 'admin.access'):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You are not allowed to access this page.")
    return wrapper

def roles_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if has_any_role(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Access denied.")
        return wrapper
    return decorator


def permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if has_role_permission(request.user, permission):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Access denied.")
        return wrapper
    return decorator
