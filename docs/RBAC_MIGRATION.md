# RBAC compatibility note

The application source of truth for frontend and application-level backend access is `accounts/rbac.py`.

Legacy role values remain valid and are mapped dynamically without rewriting existing users:

- `owner` -> `president`
- `vice_president` and `hr` -> `vp_rh`
- `secretary` -> `assistant_rh`
- `media` -> `vp_mkc`
- `events_manager` -> `vp_events`
- `partnerships` -> `vp_bd`
- `design`, `treasurer`, and `member` -> `active_member`

The older `dashboard/role_permissions.py`, `accounts/permission_model.py`,
`accounts.models.RolePermission`, and `accounts/management/commands/init_permissions.py`
remain for legacy administration and compatibility. They are not removed in this step.

Functional role assignment is managed through the President-only
`members.roles.manage` permission; it is independent of `is_staff` and
`is_superuser`. User roles are read-only in Django admin. Bureau messages use
the `bureau.messages.*` permissions and resolve recipients from current
functional roles in `accounts/rbac.py`.