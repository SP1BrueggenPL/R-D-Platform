#!/bin/bash
# Azure App Service startup command.
#
# Set it under  Configuration > Stack settings > Startup command:
#     bash startup.sh
# With that field left empty Azure/Oryx falls back to an auto-generated
# gunicorn command and this script (including the migrate below) never runs.
# That is exactly how the production database ended up without the
# inno_lab_legacystorageentry table: every read/write of Inno Session Lab's
# shared storage returned a 500 (relation does not exist) and nothing was
# ever persisted.

# Apply pending Django migrations before serving traffic. A failure is
# reported loudly but does not stop the app from starting — the rest of the
# platform should keep working while the schema problem is fixed.
python manage.py migrate --noinput || echo "WARNING: python manage.py migrate nie powiodło się - schemat bazy może być nieaktualny, patrz log powyżej."

# Oryx already collects static files at build time; this is only a safety net
# and must never block startup.
python manage.py collectstatic --noinput || echo "WARNING: collectstatic nie powiodło się."

# Several workers, otherwise one slow request (e.g. an AI label read) blocks
# everyone else. The long timeout is for those AI calls; access/error logs go
# to stdout so they show up in the App Service Log stream.
exec gunicorn rdplatform.wsgi:application \
    --bind=0.0.0.0:8000 \
    --workers 3 \
    --timeout 600 \
    --access-logfile - \
    --error-logfile -
