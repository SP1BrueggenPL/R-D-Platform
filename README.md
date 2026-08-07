# Platforma R&D (Brüggen)

Django platform for R&D processes. First module: **Inno Session Lab**
(scanning/scoring competitor products and generating transfer plans onto
production lines).

## Setup

Easiest way: double-click **`start.bat`**. First run creates the venv,
installs dependencies, sets up the database, seeds the archive, and creates
the chip-21012 admin account; every run after that just starts the server
and opens http://127.0.0.1:8000/ in your browser. Close the window (or
Ctrl+C) to stop it.

Manual setup, if you'd rather do it yourself:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env         # then fill in Azure OpenAI keys when ready

python manage.py migrate
python manage.py seed_inno_lab          # loads the 60 historical archive products
python manage.py create_admin_chip --chip 21012 --name "Administrator"

python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with chip number `21012`.

The `create_admin_chip` command prints a generated Django-admin password
(username `admin`) the first time it runs — save it, it's only shown once.
That password is only for `/admin/`; logging into the platform itself is
always just the chip number.

## Managing users and roles

Anyone with the **Administrator** role sees a "Użytkownicy" link in the top
nav (`/accounts/uzytkownicy/`) to add, edit, deactivate, or delete platform
accounts — each just needs a display name, a chip number, and a role
(Administrator or Członek zespołu R&D). No password is set; login is always
the chip number, same as everyone else. Non-admins get a 403 if they try the
URL directly. This is separate from Django's `/admin/`, which stays
username+password and is only for the couple of people who need raw
database access.

## Adding a new R&D process

1. `python manage.py startapp <your_app>`, add it to `INSTALLED_APPS`.
2. Wire its URLs into `rdplatform/urls.py`.
3. Add one entry to `core/registry.py` (`RD_PROCESSES`).

Nothing else on the hub page needs to change.

## Enabling AI (Azure OpenAI GPT-4o)

Set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` in `.env` (deployment
name defaults to `gpt-4o`). Until then, the "Odczytaj skład i wartości (AI)"
and "Uszczegółowij zadania (AI)" buttons stay disabled and every field they'd
fill in is entered by hand — the app is fully usable without AI.

## Deploying to Azure

See [DEPLOY.md](DEPLOY.md) — Postgres via `DATABASE_URL`, gunicorn, whitenoise
for static files, and Azure App Service settings are already wired up in
`rdplatform/settings.py`; nothing above changes for local dev.

## Notes on what changed vs. the original single-file tool

- Real database (SQLite by default) instead of browser localStorage — no
  more "burn a shared database", "merge JSON copy" hacks; every user hits
  the same server. A plain "Kopia JSON" export/import is kept for backups.
- Login is by chip number (`accounts` app), matching how the shop floor
  already scans badges. Django's `/admin/` still needs a username+password
  for the small admin surface (managing users/data directly).
- The pl/en/de/fr UI-translation toggle from the original tool was **not**
  ported — this deployment is Polish-only. Say if you want it back.
- SharePoint bulk-photo-import-by-filename and the radar/spider chart on the
  scoring screen were dropped as legacy/no-backend-only conveniences; ask if
  either is actually wanted and they can be added.

## Data protection

Employee identity here is only the chip number + display name needed to log
in and attribute entries — nothing else is collected. Before wider rollout,
confirm with your Data Protection Officer that storing chip number ↔ name
this way is covered (see `AUTHENTICATION_BACKENDS` in `rdplatform/settings.py`
and `accounts.Profile`).
