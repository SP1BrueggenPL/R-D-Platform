from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ChipLoginForm


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
