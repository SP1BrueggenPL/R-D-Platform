"""Read automatically by gunicorn from the app directory.

On Azure App Service the deploy runs through Oryx's auto-detected gunicorn
command whenever no Startup Command is configured; startup.sh (and the
`migrate` in it) is then never executed, so new migrations — e.g. the table
behind Inno Session Lab's shared storage — never reached the production
database and every read/write of that storage failed with a 500.

on_starting runs once in the gunicorn master before any worker is forked, so
there is no race between workers. A failure is logged and the app still
starts (the rest of the platform keeps working).
"""
import os
import traceback


def on_starting(server):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rdplatform.settings')
    try:
        import django
        from django.core.management import call_command
        from django.db import connections

        django.setup()
        call_command('migrate', interactive=False, verbosity=1)
        connections.close_all()
        server.log.info('Migracje bazy zastosowane (gunicorn.conf.py).')
    except Exception:
        server.log.error('Nie udalo sie zastosowac migracji bazy:\n%s', traceback.format_exc())
