from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings

from accounts.models import Profile

from .i18n import LANG_CODES, STRINGS, tr
from .registry import RD_PROCESSES

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


def login_as(client, chip, role):
    user = User.objects.create(username=f'chip{chip}')
    Profile.objects.create(user=user, chip_number=chip, display_name=f'U{chip}', role=role)
    client.force_login(user)
    return user


@override_settings(STORAGES=PLAIN_STORAGES)
class ProcessAccessTests(TestCase):
    INNO = '/inno-session-lab/'
    STORAGE = '/inno-session-lab/api/storage/inno:core/'

    def test_member_and_innosession_roles_see_and_open_the_process(self):
        for chip, role in (('1', Profile.ROLE_MEMBER), ('2', Profile.ROLE_INNOSESSION)):
            login_as(self.client, chip, role)
            self.assertContains(self.client.get('/'), 'Inno Session Lab')
            self.assertEqual(self.client.get(self.INNO).status_code, 200)
            self.assertEqual(self.client.get(self.STORAGE).status_code, 200)
            self.client.logout()

    def test_any_other_role_neither_sees_nor_opens_it(self):
        login_as(self.client, '3', 'guest')
        hub = self.client.get('/')
        self.assertNotContains(hub, 'Inno Session Lab')
        self.assertContains(hub, 'Twoja rola nie ma dostępu do żadnego procesu')
        self.assertEqual(self.client.get(self.INNO).status_code, 403)

    def test_the_whole_url_tree_is_guarded_not_just_the_tile(self):
        login_as(self.client, '3', 'guest')
        self.assertEqual(self.client.get(self.STORAGE).status_code, 403)
        self.assertEqual(self.client.post(self.STORAGE, data='{"value":"x"}', content_type='application/json').status_code, 403)
        self.assertEqual(self.client.post('/inno-session-lab/api/ai-proxy/', data='{}', content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get('/inno-session-lab/baza/').status_code, 403)

    def test_denied_page_is_translated(self):
        login_as(self.client, '3', 'guest')
        self.client.get('/jezyk/de/')
        self.assertContains(self.client.get(self.INNO), 'Zugriff verweigert', status_code=403)

    def test_admin_and_superuser_always_get_in(self):
        with mock.patch.dict(RD_PROCESSES[0], {'roles': ['innosession']}):
            login_as(self.client, '4', Profile.ROLE_ADMIN)
            self.assertEqual(self.client.get(self.INNO).status_code, 200)
            self.client.logout()
            boss = User.objects.create(username='boss', is_superuser=True)
            self.client.force_login(boss)
            self.assertEqual(self.client.get(self.INNO).status_code, 200)

    def test_process_can_be_narrowed_to_one_role(self):
        with mock.patch.dict(RD_PROCESSES[0], {'roles': ['innosession']}):
            login_as(self.client, '1', Profile.ROLE_MEMBER)
            self.assertEqual(self.client.get(self.INNO).status_code, 403)
            self.client.logout()
            login_as(self.client, '2', Profile.ROLE_INNOSESSION)
            self.assertEqual(self.client.get(self.INNO).status_code, 200)

    def test_anonymous_is_still_sent_to_login(self):
        r = self.client.get(self.INNO)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_innosession_is_a_selectable_role_with_a_label(self):
        self.assertIn(('innosession', 'Innosession'), Profile.ROLE_CHOICES)
        self.assertLessEqual(len(Profile.ROLE_INNOSESSION), Profile._meta.get_field('role').max_length)
