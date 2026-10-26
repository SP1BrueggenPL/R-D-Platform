from .i18n import DEFAULT_LANG, LANGUAGES
from .registry import RD_PROCESSES


def rd_processes(request):
    return {'rd_processes': RD_PROCESSES}


def language(request):
    return {'LANG': getattr(request, 'LANG', DEFAULT_LANG), 'LANGUAGES': LANGUAGES}
