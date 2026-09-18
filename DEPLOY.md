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

Deployment is via GitHub Actions (`.github/workflows/main_r-dplatform.yml`,
added by Azure's Deployment Center) — every push to `main` builds and
deploys automatically. `startup.sh` still runs migrations and collects
static files on the App Service side before starting gunicorn.

## 4. First-run admin account

The chip-`21012` admin account isn't created automatically on Azure (there's
no seed step in `startup.sh` on purpose — you don't want every redeploy
trying to recreate it). Run it once via the Web App's **SSH** console
(Development Tools > SSH in the Portal):

```bash
python manage.py seed_inno_lab
python manage.py create_admin_chip --chip 21012 --name "Administrator"
```

## The standalone Inno Session Lab file

`/inno-session-lab/` serves `inno_lab/legacy/inno_session_lab.html`.
Unlike the very first import, this file is **not** frozen byte-for-byte
anymore — once real feature/behavior changes were requested (AI wiring,
OCR prompt quality, persistence), it became a normal, version-controlled
source file like any other, editable via ordinary commits. Only the
hosting-integration bits are still patched at *serve time* (never on
disk), by `inno_lab/views.py: original_app()`:

- A "powrót do platformy" link spliced into the static top bar.
- Its `callAI()` — which posts to `api.anthropic.com` with no key, so it
  never worked standalone either — redirected to
  `/inno-session-lab/api/ai-proxy/`, which calls Azure OpenAI server-side
  (same `AZURE_OPENAI_*` settings as above) and replies in the shape the
  file already expects. No AI credentials configured → same graceful
  "wpisz ręcznie" fallback as always.
- A `window.storage.get/set` shim, backing the file's own built-in
  polling sync/merge ("wspólna baza") with the `LegacyStorageEntry` DB
  table instead of one browser's localStorage — survives restarts and
  redeploys, shared across everyone who opens the tool.

On top of that, the file's own OCR prompt (`readLabel()`/`refineLabel()`)
was tightened for reliability: it now explicitly says which photo (front
/ back-label / product / detail) each field must come from — the earlier
version asked the model to return `nazwa`/`marka`/`claims` without ever
saying where to read them from, which is a likely cause of the reported
garbage output — and the model now returns a `niepewne` array naming any
field it isn't confident about. The scan form shows a ⚠️ next to that
field's label (and next to the Skład/Tabela confidence pills when either
is under 90%), so low-confidence reads are visibly flagged instead of
silently trusted. Swapping in a future updated copy of this file is a
normal file edit + these same three serve-time integration points; there
is no separate "restore the original" step to worry about anymore.

## Known follow-up: uploaded photos

Product photos are stored on the App Service's local disk (`MEDIA_ROOT`),
which is **not persistent** across restarts, scale-outs, or redeploys. Fine
to try the app with, not fine to trust with real photos long-term. When
that matters, swap the `default` entry in `STORAGES` (`rdplatform/settings.py`)
for `django-storages`' Azure Blob backend and point it at a Blob Storage
container — say the word and this can be wired up.
