from django.urls import path
from .views import (
    dashboard_view,
    home_view,
    activity_history_view,
    manage_permissions_view,
    update_role_permission_view,
    view_role_permissions_view,
    manage_member_roles_view,
    update_member_role_view,
    contact_bureau_view,
    bureau_messages_view,
    mark_bureau_message_read_view,
    footer_settings_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('history/', activity_history_view, name='activity_history'),
    path('permissions/', manage_permissions_view, name='manage_permissions'),
    path('permissions/update/', update_role_permission_view, name='update_role_permission'),
    path('permissions/<str:role>/', view_role_permissions_view, name='view_role_permissions'),
    path('manage-member-roles/', manage_member_roles_view, name='manage_member_roles'),
    path('manage-member-roles/<int:user_id>/', update_member_role_view, name='update_member_role'),
    path('contact-bureau/', contact_bureau_view, name='contact_bureau'),
    path('bureau-messages/', bureau_messages_view, name='bureau_messages'),
    path('bureau-messages/<int:message_id>/read/', mark_bureau_message_read_view, name='mark_bureau_message_read'),
    path('footer-settings/', footer_settings_view, name='footer_settings'),
]
