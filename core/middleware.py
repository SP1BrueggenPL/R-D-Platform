from django.core.exceptions import PermissionDenied

from .access import blocked_process_for
from .i18n import DEFAULT_LANG, LANG_COOKIE, normalize_lang


class LanguageMiddleware:
    """Exposes the visitor's chosen language as `request.LANG`.

    Plain cookie (not the session): it must survive logout, which flushes the
    session, so the login page keeps the language the user picked."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.LANG = normalize_lang(request.COOKIES.get(LANG_COOKIE, DEFAULT_LANG))
        return self.get_response(request)


class ProcessAccessMiddleware:
    """Keeps users without the right role out of a restricted process's whole URL
    tree (pages, storage and AI endpoints), not just off the hub's tile list —
    otherwise a pasted link would still open it. Anonymous visitors are left to
    each view's own login_required."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and blocked_process_for(user, request.path):
            raise PermissionDenied('process access denied')
        return self.get_response(request)
