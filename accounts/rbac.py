"""Central application RBAC.

Legacy role values are intentionally retained in the database and resolved at
runtime through ROLE_ALIASES; no existing account is rewritten automatically.
"""

ROLE_ALIASES = {
    'owner': 'president',
    'vice_president': 'vp_rh',
    'hr': 'vp_rh',
    'media': 'vp_mkc',
    'events_manager': 'vp_events',
    'partnerships': 'vp_bd',
    'member': 'active_member',
    'design': 'active_member',
    'treasurer': 'active_member',
    'secretary': 'assistant_rh',
}

ROLE_LABELS = {
    'president': 'Président',
    'vp_rh': 'VP RH',
    'assistant_rh': 'Assistant RH',
    'vp_mkc': 'VP MKC',
    'assistant_comm_mkg': 'Assistant Comm/MKG',
    'vp_events': 'VP Events',
    'assistant_event': 'Assistant Événementiel',
    'vp_bd': 'VP BD',
    'assistant_bd': 'Assistant BD',
    'active_member': 'Membre Actif',
}

BUREAU_MESSAGE_RECIPIENT_ROLES = {
    'general': (
        'Bureau général',
        tuple(role for role in ROLE_LABELS if role != 'active_member'),
    ),
    'president': ('Président', ('president',)),
    'hr': ('RH', ('vp_rh', 'assistant_rh')),
    'mkc': ('MKC', ('vp_mkc', 'assistant_comm_mkg')),
    'events': ('Événementiel', ('vp_events', 'assistant_event')),
    'bd': ('BD', ('vp_bd', 'assistant_bd')),
}

ROLE_PERMISSIONS = {
    'president': {'*'},
    'vp_rh': {'members.view', 'members.manage', 'members.approve', 'events.view', 'announcements.view', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'assistant_rh': {'members.view', 'members.approve', 'events.view', 'announcements.view', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'vp_mkc': {'announcements.view', 'announcements.create', 'announcements.edit', 'announcements.approve', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'assistant_comm_mkg': {'announcements.view', 'announcements.create', 'announcements.edit_own', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'vp_events': {'events.view', 'events.create', 'events.edit', 'events.delete', 'projects.view', 'projects.create', 'projects.edit', 'projects.delete', 'announcements.view', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'assistant_event': {'events.view', 'events.create', 'events.edit', 'projects.view', 'projects.create', 'announcements.view', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'vp_bd': {'bd.view', 'bd.manage', 'events.view', 'announcements.view', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'assistant_bd': {'bd.view', 'bd.interact', 'events.view', 'announcements.view', 'assistant.use', 'bureau.messages.send', 'bureau.messages.view'},
    'active_member': {'events.view', 'events.register', 'projects.view', 'announcements.view', 'assistant.use', 'profile.view_self', 'profile.edit_self', 'bureau.messages.send'},
}


def canonical_role(role):
    return ROLE_ALIASES.get(role, role)


def role_label(role):
    return ROLE_LABELS.get(canonical_role(role), role)


def has_role_permission(user, permission):
    if not user or not user.is_authenticated:
        return False
    if permission == 'members.roles.manage':
        return canonical_role(user.role) == 'president'
    if user.is_superuser or canonical_role(user.role) == 'president':
        return True
    roles = [canonical_role(user.role)]
    if user.secondary_role:
        roles.append(canonical_role(user.secondary_role))
    return any(
        permission in ROLE_PERMISSIONS.get(role, set())
        or (permission.startswith('bd.') and 'bd.manage' in ROLE_PERMISSIONS.get(role, set()))
        for role in roles
    )


def has_functional_role(user, roles):
    if not user or not user.is_authenticated:
        return False
    allowed = {canonical_role(role) for role in roles}
    user_roles = {canonical_role(user.role)}
    if user.secondary_role:
        user_roles.add(canonical_role(user.secondary_role))
    return bool(user_roles & allowed)


def has_any_role(user, roles):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or canonical_role(user.role) == 'president':
        return True
    allowed = {canonical_role(role) for role in roles}
    user_roles = {canonical_role(user.role)}
    if user.secondary_role:
        user_roles.add(canonical_role(user.secondary_role))
    return bool(user_roles & allowed)