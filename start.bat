@echo off
setlocal
cd /d "%~dp0"

if not exist venv (
    echo Tworze srodowisko wirtualne Python...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Sprawdzam / instaluje zaleznosci...
pip install -q -r requirements.txt

if not exist db.sqlite3 (
    echo Przygotowuje baze danych...
    python manage.py migrate
    python manage.py seed_inno_lab
    python manage.py create_admin_chip --chip 21012 --name "Administrator"
) else (
    python manage.py migrate
)

echo.
echo ============================================================
echo  Platforma R^&D startuje na http://127.0.0.1:8000/
echo  Logowanie: numer chip (Admin: 21012)
echo  Zatrzymanie: zamknij to okno albo Ctrl+C
echo ============================================================
echo.

start "" http://127.0.0.1:8000/
python manage.py runserver 127.0.0.1:8000

endlocal
