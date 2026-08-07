from .registry import RD_PROCESSES


def rd_processes(request):
    return {'rd_processes': RD_PROCESSES}
