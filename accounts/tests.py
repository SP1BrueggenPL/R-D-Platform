from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Profile

LOGIN = '/accounts/login/'

# Production serves hashed static files from a manifest built by collectstatic;
# tests render templates without that step, so use the plain storage there.
PLAIN_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def make_profile(chip='40071', role=Profile.ROLE_MEMBER, code=None, active=True):
    user = User(username=f'chip{chip}')
    user.set_unusable_password()
    user.save()
    profile = Profile.objects.create(user=user, chip_number=chip, display_name=f'User {chip}',
                                     role=role, is_active_chip=active)
    if code:
        profile.set_auth_code(code)
    return profile


@override_settings(STORAGES=PLAIN_STORAGES)
class ChipLoginFlowTests(TestCase):
    def test_unknown_chip_stays_on_chip_step(self):
        r = self.client.post(LOGIN, {'step': 'chip', 'chip_number': '99999'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(r, 'name="chip_number"')

    def test_inactive_chip_is_rejected(self):
        make_profile('111', active=False, code='secret1')
        r = self.client.post(LOGIN, {'step': 'chip', 'chip_number': '111'})
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertNotContains(r, 'name="auth_code"')

    def test_first_login_asks_to_set_a_code_and_does_not_log_in(self):
        make_profile('40071')
        r = self.client.post(LOGIN, {'step': 'chip', 'chip_number': '40071'})
        self.assertContains(r, 'name="new_code"')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_setting_a_code_logs_in_and_stores_only_a_hash(self):
        profile = make_profile('40071')
        r = self.client.post(LOGIN, {'step': 'setup', 'chip_number': '40071',
                                     'new_code': 'Kod-1234', 'new_code_confirm': 'Kod-1234'})
        self.assertRedirects(r, reverse('core:hub'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), profile.user_id)
        profile.refresh_from_db()
        self.assertTrue(profile.has_auth_code)
        self.assertNotIn('Kod-1234', profile.auth_code_hash)

    def test_setup_rejects_short_mismatched_and_chip_like_codes(self):
        profile = make_profile('40071')
        for new, again in (('abc', 'abc'), ('Kod-1234', 'Kod-9999'), ('40071', '40071')):
            r = self.client.post(LOGIN, {'step': 'setup', 'chip_number': '40071',
                                         'new_code': new, 'new_code_confirm': again})
            self.assertEqual(r.status_code, 200)
            self.assertNotIn('_auth_user_id', self.client.session)
        profile.refresh_from_db()
        self.assertFalse(profile.has_auth_code)

    def test_setup_cannot_overwrite_an_existing_code(self):
        profile = make_profile('40071', code='original-code')
        self.client.post(LOGIN, {'step': 'setup', 'chip_number': '40071',
                                 'new_code': 'attacker-code', 'new_code_confirm': 'attacker-code'})
        self.assertNotIn('_auth_user_id', self.client.session)
        profile.refresh_from_db()
        self.assertTrue(profile.check_auth_code('original-code'))

    def test_chip_with_a_code_asks_for_it(self):
        make_profile('40071', code='Kod-1234')
        r = self.client.post(LOGIN, {'step': 'chip', 'chip_number': '40071'})
        self.assertContains(r, 'name="auth_code"')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_correct_and_wrong_code(self):
        profile = make_profile('40071', code='Kod-1234')
        r = self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'zly-kod'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        r = self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'Kod-1234'})
        self.assertRedirects(r, reverse('core:hub'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), profile.user_id)

    def test_chip_alone_never_logs_in(self):
        make_profile('40071', code='Kod-1234')
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': ''})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_lockout_after_repeated_wrong_codes_blocks_even_the_right_one(self):
        profile = make_profile('40071', code='Kod-1234')
        for _ in range(Profile.MAX_CODE_ATTEMPTS):
            self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'nope-nope'})
        profile.refresh_from_db()
        self.assertTrue(profile.is_code_locked)
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'Kod-1234'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_lock_expires(self):
        profile = make_profile('40071', code='Kod-1234')
        profile.code_locked_until = timezone.now() - timezone.timedelta(seconds=1)
        profile.save()
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'Kod-1234'})
        self.assertIn('_auth_user_id', self.client.session)

    def test_next_redirect_is_same_site_only(self):
        make_profile('40071', code='Kod-1234')
        r = self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'Kod-1234',
                                     'next': 'https://evil.example/phish'})
        self.assertRedirects(r, reverse('core:hub'), fetch_redirect_response=False)

    def test_next_to_a_local_page_is_followed(self):
        make_profile('40071', code='Kod-1234')
        r = self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'Kod-1234',
                                     'next': '/inno-session-lab/'})
        self.assertRedirects(r, '/inno-session-lab/', fetch_redirect_response=False)


@override_settings(STORAGES=PLAIN_STORAGES)
class ResetCodeTests(TestCase):
    def setUp(self):
        self.admin = make_profile('21012', role=Profile.ROLE_ADMIN, code='Admin-1234')
        self.member = make_profile('40071', code='Kod-1234')

    def reset_url(self, profile):
        return reverse('accounts:user_reset_code', args=[profile.pk])

    def test_admin_resets_a_forgotten_code_and_user_sets_a_new_one(self):
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '21012', 'auth_code': 'Admin-1234'})
        self.client.post(self.reset_url(self.member))
        self.member.refresh_from_db()
        self.assertFalse(self.member.has_auth_code)

        member_client = self.client_class()
        r = member_client.post(LOGIN, {'step': 'chip', 'chip_number': '40071'})
        self.assertContains(r, 'name="new_code"')
        member_client.post(LOGIN, {'step': 'setup', 'chip_number': '40071',
                                   'new_code': 'Nowy-kod-9', 'new_code_confirm': 'Nowy-kod-9'})
        self.assertIn('_auth_user_id', member_client.session)

    def test_reset_clears_a_lockout(self):
        for _ in range(Profile.MAX_CODE_ATTEMPTS):
            self.member.check_auth_code('zle-haslo')
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_code_locked)
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '21012', 'auth_code': 'Admin-1234'})
        self.client.post(self.reset_url(self.member))
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_code_locked)

    def test_member_cannot_reset_anyones_code(self):
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '40071', 'auth_code': 'Kod-1234'})
        r = self.client.post(self.reset_url(self.admin))
        self.assertEqual(r.status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.has_auth_code)

    def test_anonymous_cannot_reset(self):
        r = self.client.post(self.reset_url(self.member))
        self.assertEqual(r.status_code, 302)
        self.member.refresh_from_db()
        self.assertTrue(self.member.has_auth_code)

    def test_reset_requires_post(self):
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '21012', 'auth_code': 'Admin-1234'})
        r = self.client.get(self.reset_url(self.member))
        self.assertEqual(r.status_code, 405)

    def test_users_page_shows_code_status_and_reset_button(self):
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '21012', 'auth_code': 'Admin-1234'})
        r = self.client.get(reverse('accounts:user_list'))
        self.assertContains(r, 'Resetuj kod')
        self.assertContains(r, 'ustawiony')

    def test_users_page_has_a_way_back_to_the_processes_hub(self):
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '21012', 'auth_code': 'Admin-1234'})
        for url in (reverse('accounts:user_list'), reverse('accounts:user_create')):
            r = self.client.get(url)
            self.assertContains(r, f'<a href="{reverse("core:hub")}">← Procesy</a>', html=True)
        self.assertNotContains(self.client.get(reverse('core:hub')), '← Procesy')

    def test_admin_can_create_a_user_with_the_innosession_role(self):
        self.client.post(LOGIN, {'step': 'code', 'chip_number': '21012', 'auth_code': 'Admin-1234'})
        r = self.client.post(reverse('accounts:user_create'), {
            'display_name': 'Ewa Inno', 'chip_number': '55555', 'role': 'innosession', 'is_active_chip': 'on'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Profile.objects.get(chip_number='55555').role, Profile.ROLE_INNOSESSION)
        self.assertContains(self.client.get(reverse('accounts:user_list')), 'Innosession')
