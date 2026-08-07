from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_MEMBER, 'Członek zespołu R&D'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    chip_number = models.CharField(
        max_length=20, unique=True, verbose_name='Numer chip',
        help_text='Numer identyfikacyjny karty / chipa pracownika używany do logowania.',
    )
    display_name = models.CharField(max_length=150, blank=True, default='', verbose_name='Nazwa wyświetlana')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER, verbose_name='Rola')
    is_active_chip = models.BooleanField(default=True, verbose_name='Chip aktywny')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Profil (chip)'
        verbose_name_plural = 'Profile (chip)'

    def __str__(self):
        return f'{self.display_name or self.user.username} (chip {self.chip_number})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN
