"""Small built-in translation layer for the platform shell (login page, hub,
top bar): Polish, English, German, French.

Deliberately not gettext: that needs compiled .mo files (msgfmt) in the
Azure build. A dict keeps translations next to the code and works anywhere.

The chosen language lives in the `rd_lang` cookie (set by core.views.set_language),
read by core.middleware.LanguageMiddleware into `request.LANG`.
"""

DEFAULT_LANG = 'pl'
LANG_COOKIE = 'rd_lang'
LANG_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

# (code, short label, native name)
LANGUAGES = [
    ('pl', 'PL', 'Polski'),
    ('en', 'EN', 'English'),
    ('de', 'DE', 'Deutsch'),
    ('fr', 'FR', 'Français'),
]
LANG_CODES = [code for code, _short, _name in LANGUAGES]


def _s(pl, en, de, fr):
    return {'pl': pl, 'en': en, 'de': de, 'fr': fr}


STRINGS = {
    # ---- top bar -----------------------------------------------------------
    'nav.users': _s('Użytkownicy', 'Users', 'Benutzer', 'Utilisateurs'),
    'nav.admin': _s('Admin', 'Admin', 'Admin', 'Admin'),
    'nav.logout': _s('Wyloguj', 'Log out', 'Abmelden', 'Déconnexion'),
    'nav.language': _s('Język', 'Language', 'Sprache', 'Langue'),

    # ---- login -------------------------------------------------------------
    'login.title': _s('Logowanie', 'Sign in', 'Anmeldung', 'Connexion'),
    'login.heading': _s('Logowanie chipem', 'Sign in with your chip', 'Anmeldung mit Chip', 'Connexion par puce'),
    'login.intro': _s(
        'Wpisz swój numer chip, aby zalogować się do platformy.',
        'Enter your chip number to sign in to the platform.',
        'Geben Sie Ihre Chipnummer ein, um sich bei der Plattform anzumelden.',
        'Saisissez votre numéro de puce pour vous connecter à la plateforme.',
    ),
    'login.chip_label': _s('Numer chip', 'Chip number', 'Chipnummer', 'Numéro de puce'),
    'login.continue': _s('Dalej', 'Continue', 'Weiter', 'Continuer'),
    'login.other_chip': _s('← Inny numer chip', '← Different chip number', '← Andere Chipnummer', '← Autre numéro de puce'),

    'login.code.heading': _s('Kod autoryzacyjny', 'Authorization code', 'Autorisierungscode', "Code d'autorisation"),
    'login.code.intro': _s(
        'Chip %(chip)s — wpisz swój kod autoryzacyjny, aby potwierdzić logowanie.',
        'Chip %(chip)s — enter your authorization code to confirm sign-in.',
        'Chip %(chip)s – geben Sie Ihren Autorisierungscode ein, um die Anmeldung zu bestätigen.',
        "Puce %(chip)s — saisissez votre code d'autorisation pour confirmer la connexion.",
    ),
    'login.code.label': _s('Kod autoryzacyjny', 'Authorization code', 'Autorisierungscode', "Code d'autorisation"),
    'login.code.submit': _s('Zaloguj', 'Sign in', 'Anmelden', 'Se connecter'),
    'login.code.forgot': _s(
        'Nie pamiętasz kodu? Poproś administratora o jego reset.',
        'Forgot your code? Ask an administrator to reset it.',
        'Code vergessen? Bitten Sie einen Administrator, ihn zurückzusetzen.',
        "Code oublié ? Demandez à un administrateur de le réinitialiser.",
    ),

    'login.setup.heading': _s(
        'Ustaw kod autoryzacyjny', 'Set your authorization code',
        'Autorisierungscode festlegen', "Définir votre code d'autorisation",
    ),
    'login.setup.intro': _s(
        'To Twoje pierwsze logowanie chipem %(chip)s. Ustaw własny kod autoryzacyjny — '
        'będziesz go podawać przy każdym kolejnym logowaniu.',
        'This is your first sign-in with chip %(chip)s. Set your own authorization code — '
        'you will enter it every time you sign in.',
        'Dies ist Ihre erste Anmeldung mit Chip %(chip)s. Legen Sie Ihren eigenen Autorisierungscode fest – '
        'Sie geben ihn bei jeder weiteren Anmeldung ein.',
        "C'est votre première connexion avec la puce %(chip)s. Définissez votre propre code d'autorisation — "
        "vous le saisirez à chaque connexion.",
    ),
    'login.setup.new': _s(
        'Nowy kod (min. %(min)s znaków)', 'New code (min. %(min)s characters)',
        'Neuer Code (mind. %(min)s Zeichen)', 'Nouveau code (min. %(min)s caractères)',
    ),
    'login.setup.confirm': _s('Powtórz kod', 'Repeat code', 'Code wiederholen', 'Répétez le code'),
    'login.setup.submit': _s(
        'Zapisz kod i zaloguj', 'Save code and sign in',
        'Code speichern und anmelden', 'Enregistrer le code et se connecter',
    ),

    'login.err.unknown_chip': _s(
        'Nieznany lub nieaktywny numer chip. Sprawdź numer albo skontaktuj się z administratorem.',
        'Unknown or inactive chip number. Check the number or contact an administrator.',
        'Unbekannte oder inaktive Chipnummer. Prüfen Sie die Nummer oder wenden Sie sich an einen Administrator.',
        'Numéro de puce inconnu ou inactif. Vérifiez le numéro ou contactez un administrateur.',
    ),
    'login.err.code_short': _s(
        'Kod musi mieć co najmniej %(min)s znaków.',
        'The code must be at least %(min)s characters long.',
        'Der Code muss mindestens %(min)s Zeichen lang sein.',
        'Le code doit comporter au moins %(min)s caractères.',
    ),
    'login.err.code_mismatch': _s(
        'Kody nie są takie same.', 'The codes do not match.',
        'Die Codes stimmen nicht überein.', 'Les codes ne correspondent pas.',
    ),
    'login.err.code_is_chip': _s(
        'Kod nie może być taki sam jak numer chip.',
        'The code must not be the same as the chip number.',
        'Der Code darf nicht mit der Chipnummer identisch sein.',
        'Le code ne doit pas être identique au numéro de puce.',
    ),
    'login.err.code_wrong': _s(
        'Nieprawidłowy kod autoryzacyjny. Pozostało prób: %(left)s.',
        'Incorrect authorization code. Attempts left: %(left)s.',
        'Falscher Autorisierungscode. Verbleibende Versuche: %(left)s.',
        "Code d'autorisation incorrect. Tentatives restantes : %(left)s.",
    ),
    'login.err.code_locked': _s(
        'Zbyt wiele błędnych prób. Logowanie tym chipem jest zablokowane na %(min)s min.',
        'Too many failed attempts. Signing in with this chip is locked for %(min)s min.',
        'Zu viele Fehlversuche. Die Anmeldung mit diesem Chip ist für %(min)s Min. gesperrt.',
        'Trop de tentatives échouées. La connexion avec cette puce est verrouillée pendant %(min)s min.',
    ),

    # ---- hub ---------------------------------------------------------------
    'hub.title': _s('Procesy R&D', 'R&D processes', 'F&E-Prozesse', 'Processus R&D'),
    'hub.heading': _s('Procesy', 'Processes', 'Prozesse', 'Processus'),
    'hub.intro': _s(
        'Wybierz proces, w którym chcesz pracować. Nowe procesy będą dodawane tutaj.',
        'Choose the process you want to work in. New processes will be added here.',
        'Wählen Sie den Prozess, in dem Sie arbeiten möchten. Neue Prozesse werden hier ergänzt.',
        'Choisissez le processus dans lequel vous souhaitez travailler. De nouveaux processus seront ajoutés ici.',
    ),
    'hub.soon': _s('Wkrótce', 'Coming soon', 'Demnächst', 'Bientôt'),
}


def normalize_lang(code):
    return code if code in LANG_CODES else DEFAULT_LANG


def tr(lang, key, **params):
    """Translate `key` into `lang` (falls back to Polish, then to the key)."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry[DEFAULT_LANG]
    return text % params if params else text


def pick(value, lang):
    """Pick a language from a {'pl': ..., 'en': ...} dict (or return a plain string unchanged)."""
    if isinstance(value, dict):
        return value.get(lang) or value.get(DEFAULT_LANG) or ''
    return value
