from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.i18n import tr

from .forms import UserAccountForm
from .models import Profile


def _safe_next(request):
    target = request.POST.get('next') or request.GET.get('next') or ''
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                  require_https=request.is_secure()):
        return target
    return 'core:hub'


def chip_login(request):
    """Chip sign-in in up to two steps.

    1. chip number
    2. either the user's authorization code, or — on the very first sign-in
       (or after an admin reset) — choosing one.
    The chip is carried between steps in a hidden field; every step re-checks
    everything server-side, so nothing the browser sends is trusted.
    """
    if request.user.is_authenticated:
        return redirect('core:hub')

    lang = request.LANG
    ctx = {'stage': 'chip', 'chip': '', 'next': request.POST.get('next') or request.GET.get('next', ''),
           'min_code': Profile.MIN_CODE_LENGTH}

    if request.method == 'POST':
        step = request.POST.get('step', 'chip')
        chip = (request.POST.get('chip_number') or '').strip()
        profile = (Profile.objects.select_related('user')
                   .filter(chip_number=chip, is_active_chip=True).first()) if chip else None

        if profile is None:
            messages.error(request, tr(lang, 'login.err.unknown_chip'))
            ctx['chip'] = chip
        elif not profile.has_auth_code:
            ctx.update(stage='setup', chip=chip)
            if step == 'setup':
                code = request.POST.get('new_code') or ''
                again = request.POST.get('new_code_confirm') or ''
                if len(code) < Profile.MIN_CODE_LENGTH:
                    messages.error(request, tr(lang, 'login.err.code_short', min=Profile.MIN_CODE_LENGTH))
                elif code != again:
                    messages.error(request, tr(lang, 'login.err.code_mismatch'))
                elif code == chip:
                    messages.error(request, tr(lang, 'login.err.code_is_chip'))
                else:
                    profile.set_auth_code(code)
                    user = authenticate(request, chip_number=chip, auth_code=code)
                    if user is not None:
                        login(request, user)
                        return redirect(_safe_next(request))
        else:
            ctx.update(stage='code', chip=chip)
            if step == 'code':
                if profile.is_code_locked:
                    messages.error(request, tr(lang, 'login.err.code_locked', min=profile.lock_minutes_left))
                else:
                    user = authenticate(request, chip_number=chip, auth_code=request.POST.get('auth_code') or '')
                    if user is not None:
                        login(request, user)
                        return redirect(_safe_next(request))
                    profile.refresh_from_db()
                    if profile.is_code_locked:
                        messages.error(request, tr(lang, 'login.err.code_locked', min=profile.lock_minutes_left))
                    else:
                        messages.error(request, tr(lang, 'login.err.code_wrong', left=profile.attempts_left))

    return render(request, 'accounts/login.html', ctx)


@require_POST
@login_required
def chip_logout(request):
    logout(request)
    return redirect('accounts:login')


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        if not (profile and profile.is_admin):
            raise PermissionDenied('Ta sekcja jest dostępna tylko dla administratorów.')
        return view_func(request, *args, **kwargs)
    return wrapper


# --------------------------------------------------------------------------
# User management (admin role only)
# --------------------------------------------------------------------------

@admin_required
def user_list(request):
    profiles = Profile.objects.select_related('user').order_by('display_name', 'chip_number')
    return render(request, 'accounts/user_list.html', {'profiles': profiles})


@admin_required
def user_create(request):
    form = UserAccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        chip_number = form.cleaned_data['chip_number']
        username = f"chip{chip_number}"
        user = User(username=username)
        user.set_unusable_password()
        user.save()
        Profile.objects.create(
            user=user,
            chip_number=chip_number,
            display_name=form.cleaned_data['display_name'],
            role=form.cleaned_data['role'],
            is_active_chip=form.cleaned_data['is_active_chip'],
        )
        messages.success(request, f"Konto \"{form.cleaned_data['display_name']}\" (chip {chip_number}) utworzone. "
                                  "Przy pierwszym logowaniu użytkownik ustawi własny kod autoryzacyjny.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'profile': None})


@admin_required
def user_edit(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    form = UserAccountForm(request.POST or None, profile=profile)
    if request.method == 'POST' and form.is_valid():
        profile.chip_number = form.cleaned_data['chip_number']
        profile.display_name = form.cleaned_data['display_name']
        profile.role = form.cleaned_data['role']
        profile.is_active_chip = form.cleaned_data['is_active_chip']
        profile.save()
        messages.success(request, 'Zmiany zapisane.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'profile': profile})


@admin_required
@require_POST
def user_toggle_active(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if profile.user_id == request.user.id:
        messages.error(request, 'Nie możesz dezaktywować własnego konta.')
    else:
        profile.is_active_chip = not profile.is_active_chip
        profile.save(update_fields=['is_active_chip'])
        messages.success(request, f"Chip {profile.chip_number} {'aktywowany' if profile.is_active_chip else 'dezaktywowany'}.")
    return redirect('accounts:user_list')


@admin_required
@require_POST
def user_delete(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if profile.user_id == request.user.id:
        messages.error(request, 'Nie możesz usunąć własnego konta.')
    else:
        display = f'{profile.display_name} (chip {profile.chip_number})'
        profile.user.delete()
        messages.success(request, f'Konto {display} usunięte.')
    return redirect('accounts:user_list')


@admin_required
@require_POST
def user_reset_code(request, pk):
    """Forgotten authorization code: clear it so the user picks a new one at their next chip sign-in."""
    profile = get_object_or_404(Profile, pk=pk)
    profile.reset_auth_code()
    messages.success(request, f'Kod autoryzacyjny użytkownika {profile.display_name or profile.user.username} '
                              f'(chip {profile.chip_number}) zresetowany — przy następnym logowaniu ustawi nowy.')
    return redirect('accounts:user_list')
