from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from events.models import Event
from announcements.models import Announcement
from accounts.models import User as CustomUser
from dashboard.models import ActivityLog
import json

User = get_user_model()


def get_request_info(instance):
    """Extract IP and user agent if available"""
    ip = None
    user_agent = ""
    
    # Try to get from middleware context if available
    if hasattr(instance, '_request'):
        request = instance._request
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    return ip, user_agent


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def truncate_text(text, words=50):
    """Truncate text to specified number of words"""
    if not text:
        return ""
    word_list = text.split()
    if len(word_list) <= words:
        return text
    return ' '.join(word_list[:words]) + '...'


@receiver(post_save, sender=Event)
def log_event_changes(sender, instance, created, **kwargs):
    """Log Event creation and updates"""
    action = 'create' if created else 'update'
    
    try:
        user = kwargs.get('request').user if hasattr(kwargs.get('request', None), 'user') else None
    except:
        user = None
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        content_type='Event',
        object_id=instance.id,
        object_name=instance.title,
        new_value=f"Événement: {instance.title}\nDate: {instance.date}\nLieu: {instance.location}",
    )


@receiver(post_save, sender=Announcement)
def log_announcement_changes(sender, instance, created, **kwargs):
    """Log Announcement creation and updates"""
    action = 'create' if created else 'update'
    
    try:
        user = kwargs.get('request').user if hasattr(kwargs.get('request', None), 'user') else None
    except:
        user = None
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        content_type='Announcement',
        object_id=instance.id,
        object_name=instance.title,
        new_value=truncate_text(instance.content, 50),
    )


@receiver(post_save, sender=CustomUser)
def log_user_creation(sender, instance, created, **kwargs):
    """Log user registration"""
    if created:
        ActivityLog.objects.create(
            user=instance,
            action='register',
            content_type='User',
            object_id=instance.id,
            object_name=f"{instance.first_name} {instance.last_name}",
            new_value=f"Rôle: {instance.role}",
        )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login"""
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    ActivityLog.objects.create(
        user=user,
        action='login',
        content_type='User',
        object_id=user.id,
        object_name=f"{user.first_name} {user.last_name}" or user.username,
        ip_address=ip,
        user_agent=user_agent,
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user is None or not user.is_authenticated:
        return

    ip = get_client_ip(request)
    
    ActivityLog.objects.create(
        user=user,
        action='logout',
        content_type='User',
        object_id=user.id,
        object_name=f"{user.first_name} {user.last_name}" or user.username,
        ip_address=ip,
    )
