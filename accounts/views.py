from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ChipLoginForm, UserAccountForm
from .models import Profile


def chip_login(request):
    if request.user.is_authenticated:
        return redirect('core:hub')

    form = ChipLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        chip_number = form.cleaned_data['chip_number']
        user = authenticate(request, chip_number=chip_number)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'core:hub'
            return redirect(next_url)
        messages.error(request, 'Nieznany lub nieaktywny numer chip. Sprawdź numer albo skontaktuj się z administratorem.')

    return render(request, 'accounts/login.html', {'form': form, 'next': request.GET.get('next', '')})


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
        messages.success(request, f"Konto \"{form.cleaned_data['display_name']}\" (chip {chip_number}) utworzone.")
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
