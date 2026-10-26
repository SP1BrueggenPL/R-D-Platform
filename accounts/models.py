import datetime

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_INNOSESSION = 'innosession'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_MEMBER, 'Członek zespołu R&D'),
        (ROLE_INNOSESSION, 'Innosession'),
    ]

    # Authorization code (second factor for chip sign-in).
    MIN_CODE_LENGTH = 6
    MAX_CODE_ATTEMPTS = 5
    CODE_LOCK_MINUTES = 15

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    chip_number = models.CharField(
        max_length=20, unique=True, verbose_name='Numer chip',
        help_text='Numer identyfikacyjny karty / chipa pracownika używany do logowania.',
    )
    display_name = models.CharField(max_length=150, blank=True, default='', verbose_name='Nazwa wyświetlana')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER, verbose_name='Rola')
    is_active_chip = models.BooleanField(default=True, verbose_name='Chip aktywny')
    created_at = models.DateTimeField(auto_now_add=True)

    # Never the code itself — a Django password hash. Empty = not set yet, so the
    # next chip sign-in makes the user choose one (also how an admin reset works).
    auth_code_hash = models.CharField(max_length=255, blank=True, default='', editable=False)
    code_failed_attempts = models.PositiveSmallIntegerField(default=0, editable=False)
    code_locked_until = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = 'Profil (chip)'
        verbose_name_plural = 'Profile (chip)'

    def __str__(self):
        return f'{self.display_name or self.user.username} (chip {self.chip_number})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    # ---- authorization code ------------------------------------------------

    @property
    def has_auth_code(self):
        return bool(self.auth_code_hash)

    @property
    def is_code_locked(self):
        return bool(self.code_locked_until and self.code_locked_until > timezone.now())

    @property
    def lock_minutes_left(self):
        if not self.is_code_locked:
            return 0
        return max(1, -(-int((self.code_locked_until - timezone.now()).total_seconds()) // 60))

    @property
    def attempts_left(self):
        return max(0, self.MAX_CODE_ATTEMPTS - self.code_failed_attempts)

    def set_auth_code(self, raw_code):
        self.auth_code_hash = make_password(raw_code)
        self.code_failed_attempts = 0
        self.code_locked_until = None
        self.save(update_fields=['auth_code_hash', 'code_failed_attempts', 'code_locked_until'])

    def reset_auth_code(self):
        """Forgotten code: clear it, so the next chip sign-in asks for a new one."""
        self.auth_code_hash = ''
        self.code_failed_attempts = 0
        self.code_locked_until = None
        self.save(update_fields=['auth_code_hash', 'code_failed_attempts', 'code_locked_until'])

    def check_auth_code(self, raw_code):
        """True if the code is right. Counts failures and locks the chip for a while
        after MAX_CODE_ATTEMPTS wrong tries in a row (a short code can be guessed)."""
        if not self.has_auth_code or self.is_code_locked or not raw_code:
            return False
        if check_password(raw_code, self.auth_code_hash):
            if self.code_failed_attempts or self.code_locked_until:
                self.code_failed_attempts = 0
                self.code_locked_until = None
                self.save(update_fields=['code_failed_attempts', 'code_locked_until'])
            return True
        self.code_failed_attempts += 1
        if self.code_failed_attempts >= self.MAX_CODE_ATTEMPTS:
            self.code_locked_until = timezone.now() + datetime.timedelta(minutes=self.CODE_LOCK_MINUTES)
            self.code_failed_attempts = 0
        self.save(update_fields=['code_failed_attempts', 'code_locked_until'])
        return False
