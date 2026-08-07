#!/bin/bash
# Azure App Service (Linux, Python) startup command.
# Paste as the Startup Command in Configuration > General settings:
#   bash startup.sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

gunicorn rdplatform.wsgi:application \
    --bind=0.0.0.0:8000 \
    --timeout 600 \
    --workers 3
