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
