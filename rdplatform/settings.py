"""
Django settings for Brüggen Digital R&D.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# .env is optional — only loaded if python-dotenv is installed and the file exists.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


def env_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-t&8viqzg9x=jbl(8fp_7b32d68*qz$nlm%#1$^h%!7(+ytq(=k')

DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Azure App Service sets WEBSITE_HOSTNAME to the *.azurewebsites.net (or bound
# custom domain) the app is actually served from — trust it automatically so
# ALLOWED_HOSTS/CSRF don't need manual upkeep per environment.
_azure_hostname = os.environ.get('WEBSITE_HOSTNAME')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
if _azure_hostname:
    ALLOWED_HOSTS.append(_azure_hostname)
    CSRF_TRUSTED_ORIGINS.append(f'https://{_azure_hostname}')

# Azure App Service terminates TLS at the load balancer and forwards plain
# HTTP internally with X-Forwarded-Proto set — without this Django thinks
# every request (including HTTPS ones) is insecure.
if _azure_hostname:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts',
    'core',
    'inno_lab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rdplatform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.rd_processes',
            ],
        },
    },
]

WSGI_APPLICATION = 'rdplatform.wsgi.application'


# Postgres in production via DATABASE_URL (Azure App Service / Azure Database
# for PostgreSQL supply this as a connection string). Falls back to local
# SQLite when DATABASE_URL isn't set, so local dev needs no extra setup.
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'accounts.backends.ChipNumberBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:hub'
LOGOUT_REDIRECT_URL = 'accounts:login'


LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Uploaded photos land on the App Service's local disk, which is NOT
# persistent across restarts/scale-outs/deploys. Fine for a first deploy —
# swap the 'default' STORAGES backend above for django-storages' Azure Blob
# backend before this holds real photos long-term.
if _azure_hostname and not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ---------------------------------------------------------------------------
# Azure OpenAI (GPT-4o) — AI features (label reading, plan enrichment).
# Left disabled until credentials are provided; the app degrades gracefully
# (manual entry always works) exactly like the original Inno Session Lab tool.
# ---------------------------------------------------------------------------
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_KEY', '')
AZURE_OPENAI_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
AI_FEATURES_ENABLED = bool(AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY)

MESSAGE_TAGS = {
    'error': 'bad',
}
