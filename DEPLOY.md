# Deploying to Azure

This repo is ready for **Azure App Service (Linux, Python)** + **Azure
Database for PostgreSQL**. It still runs locally on SQLite with zero config
— nothing here is required for local dev (see [README.md](README.md)).

## 1. Azure Database for PostgreSQL

Create a Flexible Server instance and a database (e.g. `rdplatform`). Note
the connection string — you'll set it as `DATABASE_URL`:

```
postgresql://<user>:<password>@<server>.postgres.database.azure.com:5432/<dbname>?sslmode=require
```

## 2. Azure App Service

Create a Web App: **Runtime stack** = Python 3.12+ (matches this repo's
target), **OS** = Linux.

**Configuration > General settings > Startup Command:**
```
bash startup.sh
```
(`startup.sh` runs migrations, collects static files, then starts gunicorn —
nothing to configure by hand on each deploy.)

**Configuration > Application settings** (environment variables), required:

| Name | Value |
|---|---|
| `SECRET_KEY` | a long random string (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DJANGO_DEBUG` | `False` |
| `DATABASE_URL` | the Postgres connection string from step 1 |

`WEBSITE_HOSTNAME` is already set automatically by App Service — settings.py
picks it up to configure `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and the
HTTPS proxy headers, so you don't need to set those yourself unless you're
on a custom domain (then add `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain`).

Optional, to turn on the AI features (Azure OpenAI GPT-4o):

| Name | Value |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | e.g. `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | from the Azure OpenAI resource |
| `AZURE_OPENAI_DEPLOYMENT` | your GPT-4o deployment name (default `gpt-4o`) |
| `AZURE_OPENAI_API_VERSION` | default `2024-08-01-preview` is usually fine |

## 3. Deploy

Point the Web App's deployment source at this GitHub repo (Deployment
Center > GitHub) and pick the `main` branch — Azure builds and runs
`startup.sh` on every push. No GitHub Actions workflow is included in this
repo (kept deploy config on the Azure side); ask if you'd rather have a
push-triggered Actions workflow instead.

## 4. First-run admin account

The chip-`21012` admin account isn't created automatically on Azure (there's
no seed step in `startup.sh` on purpose — you don't want every redeploy
trying to recreate it). Run it once via the Web App's **SSH** console
(Development Tools > SSH in the Portal):

```bash
python manage.py seed_inno_lab
python manage.py create_admin_chip --chip 21012 --name "Administrator"
```

## Known follow-up: uploaded photos

Product photos are stored on the App Service's local disk (`MEDIA_ROOT`),
which is **not persistent** across restarts, scale-outs, or redeploys. Fine
to try the app with, not fine to trust with real photos long-term. When
that matters, swap the `default` entry in `STORAGES` (`rdplatform/settings.py`)
for `django-storages`' Azure Blob backend and point it at a Blob Storage
container — say the word and this can be wired up.
