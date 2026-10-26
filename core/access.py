"""Who may see/open which process on the hub (see `roles` in core.registry)."""
from django.urls import reverse

from .registry import RD_PROCESSES


def can_access(user, process):
    roles = process.get('roles')
    if not roles:
        return True
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    if profile is None:
        return False
    return profile.is_admin or profile.role in roles


def accessible_processes(user):
    return [p for p in RD_PROCESSES if can_access(user, p)]


def blocked_process_for(user, path):
    """The restricted process whose URL tree `path` is in and which `user` may not open, else None."""
    for process in RD_PROCESSES:
        if not process.get('roles') or can_access(user, process):
            continue
        if path.startswith(reverse(process['url_name'])):
            return process
    return None
