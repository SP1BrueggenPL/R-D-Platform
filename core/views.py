from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .i18n import LANG_CODES, LANG_COOKIE, LANG_COOKIE_MAX_AGE
from .registry import RD_PROCESSES


@login_required
def hub(request):
    return render(request, 'core/hub.html', {'processes': RD_PROCESSES})


def set_language(request, code):
    """Remember the visitor's language in a cookie and go back where they were.
    Open to anonymous visitors — the login page needs it too."""
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        next_url = reverse('core:hub')
    response = redirect(next_url)
    if code in LANG_CODES:
        response.set_cookie(LANG_COOKIE, code, max_age=LANG_COOKIE_MAX_AGE, samesite='Lax',
                            secure=request.is_secure())
    return response
