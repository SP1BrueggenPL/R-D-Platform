from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from .models import Profile


class ChipNumberBackend(BaseBackend):
    """Authenticates by chip number plus the user's own authorization code.

    Mirrors the badge/chip-scan login used on the shop floor: the employee
    types the chip number and then confirms with the personal code they chose
    at their first sign-in. Both must match, the chip must be active and not
    locked after repeated wrong codes (see Profile.check_auth_code).
    """

    def authenticate(self, request, chip_number=None, auth_code=None, **kwargs):
        if not chip_number or not auth_code:
            return None
        try:
            profile = Profile.objects.select_related('user').get(
                chip_number=chip_number.strip(), is_active_chip=True,
            )
        except Profile.DoesNotExist:
            return None
        if not profile.check_auth_code(auth_code):
            return None
        return profile.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
