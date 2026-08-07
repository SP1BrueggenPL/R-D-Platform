import secrets

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile


class Command(BaseCommand):
    help = 'Create (or update) the platform Admin account tied to a chip number.'

    def add_arguments(self, parser):
        parser.add_argument('--chip', default='21012', help='Chip number for the admin account (default: 21012).')
        parser.add_argument('--username', default='admin', help='Django username for /admin/ access (default: admin).')
        parser.add_argument('--name', default='Administrator', help='Display name.')

    def handle(self, *args, **options):
        chip = options['chip']
        username = options['username']
        display_name = options['name']

        user, user_created = User.objects.get_or_create(username=username, defaults={
            'is_staff': True, 'is_superuser': True,
        })
        password = None
        if user_created:
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()

        profile, profile_created = Profile.objects.get_or_create(user=user, defaults={
            'chip_number': chip, 'display_name': display_name, 'role': Profile.ROLE_ADMIN,
        })
        if not profile_created:
            profile.chip_number = chip
            profile.display_name = display_name
            profile.role = Profile.ROLE_ADMIN
            profile.is_active_chip = True
            profile.save()

        self.stdout.write(self.style.SUCCESS(f'Konto Admina gotowe: chip {chip}, użytkownik "{username}".'))
        if password:
            self.stdout.write(self.style.WARNING(
                f'Wygenerowane hasło do panelu /admin/ (username={username}): {password}\n'
                'Zapisz je i zmień po pierwszym logowaniu — do samej platformy R&D logowanie odbywa się numerem chipa.'
            ))
        else:
            self.stdout.write('Konto już istniało — hasło do /admin/ pozostaje bez zmian.')
