from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings

from accounts.models import Profile

from .i18n import LANG_CODES, STRINGS, tr

# Production serves hashed static files from a manifest built by collectstatic;
# tests render templates without that step, so use the plain storage there.
PLAIN_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


class TranslationTableTests(SimpleTestCase):
    def test_every_string_exists_in_all_four_languages(self):
        for key, entry in STRINGS.items():
            for code in LANG_CODES:
                self.assertTrue(entry.get(code), f'{key} missing for {code}')

    def test_format_placeholders_match_across_languages(self):
        import re
        for key, entry in STRINGS.items():
            names = {code: sorted(re.findall(r'%\((\w+)\)s', entry[code])) for code in LANG_CODES}
            self.assertEqual(len({tuple(v) for v in names.values()}), 1, f'{key}: {names}')

    def test_unknown_language_falls_back_to_polish(self):
        self.assertEqual(tr('xx', 'nav.logout'), 'Wyloguj')


@override_settings(STORAGES=PLAIN_STORAGES)
class LanguageSwitchingTests(TestCase):
    def test_login_page_in_each_language(self):
        expected = {'pl': 'Logowanie chipem', 'en': 'Sign in with your chip',
                    'de': 'Anmeldung mit Chip', 'fr': 'Connexion par puce'}
        for code, heading in expected.items():
            self.client.get(f'/jezyk/{code}/')
            r = self.client.get('/accounts/login/')
            self.assertContains(r, heading)
            self.assertContains(r, f'<html lang="{code}">')

    def test_default_is_polish(self):
        self.assertContains(self.client.get('/accounts/login/'), 'Logowanie chipem')

    def test_choice_survives_logout(self):
        user = User.objects.create(username='chip1')
        Profile.objects.create(user=user, chip_number='1', display_name='U')
        self.client.get('/jezyk/de/')
        self.client.force_login(user)
        self.client.post('/accounts/logout/')
        self.assertContains(self.client.get('/accounts/login/'), 'Anmeldung mit Chip')

    def test_hub_is_translated(self):
        user = User.objects.create(username='chip1')
        Profile.objects.create(user=user, chip_number='1', display_name='U')
        self.client.force_login(user)
        for code, heading, logout in (('en', 'Processes', 'Log out'), ('de', 'Prozesse', 'Abmelden'),
                                      ('fr', 'Processus', 'Déconnexion'), ('pl', 'Procesy', 'Wyloguj')):
            self.client.get(f'/jezyk/{code}/')
            r = self.client.get('/')
            self.assertContains(r, f'<h2>{heading}</h2>', html=True)
            self.assertContains(r, logout)

    def test_hub_process_card_is_translated(self):
        user = User.objects.create(username='chip1')
        Profile.objects.create(user=user, chip_number='1', display_name='U')
        self.client.force_login(user)
        self.client.get('/jezyk/de/')
        self.assertContains(self.client.get('/'), 'Scannen — bewerten')

    def test_invalid_language_code_is_ignored(self):
        r = self.client.get('/jezyk/xx/')
        self.assertNotIn('rd_lang', r.cookies)

    def test_open_redirect_is_blocked(self):
        r = self.client.get('/jezyk/en/?next=https://evil.example/x')
        self.assertEqual(r['Location'], '/')
        r = self.client.get('/jezyk/en/?next=/accounts/login/')
        self.assertEqual(r['Location'], '/accounts/login/')
