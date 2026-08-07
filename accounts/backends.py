from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from .models import Profile


class ChipNumberBackend(BaseBackend):
    """Authenticates purely by chip number — no password.

    Mirrors the badge/chip-scan login used on the shop floor: an employee
    (or the admin account) types their chip number and is signed in as the
    matching user, provided the chip is marked active.
    """

    def authenticate(self, request, chip_number=None, **kwargs):
        if not chip_number:
            return None
        try:
            profile = Profile.objects.select_related('user').get(
                chip_number=chip_number.strip(), is_active_chip=True,
            )
        except Profile.DoesNotExist:
            return None
        return profile.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
