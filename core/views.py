from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .registry import RD_PROCESSES


@login_required
def hub(request):
    return render(request, 'core/hub.html', {'processes': RD_PROCESSES})
