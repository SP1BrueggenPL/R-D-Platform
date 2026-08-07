from django import forms

from .models import Profile


class ChipLoginForm(forms.Form):
    chip_number = forms.CharField(
        label='Numer chip',
        max_length=20,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'inputmode': 'numeric',
            'placeholder': 'np. 40071',
            'autocomplete': 'off',
        }),
    )


class UserAccountForm(forms.Form):
    display_name = forms.CharField(label='Nazwa wyświetlana', max_length=150)
    chip_number = forms.CharField(
        label='Numer chip', max_length=20,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'off'}),
    )
    role = forms.ChoiceField(label='Rola', choices=Profile.ROLE_CHOICES)
    is_active_chip = forms.BooleanField(label='Chip aktywny', required=False, initial=True)

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        if profile is not None:
            self.fields['display_name'].initial = profile.display_name
            self.fields['chip_number'].initial = profile.chip_number
            self.fields['role'].initial = profile.role
            self.fields['is_active_chip'].initial = profile.is_active_chip

    def clean_chip_number(self):
        chip_number = self.cleaned_data['chip_number'].strip()
        qs = Profile.objects.filter(chip_number=chip_number)
        if self.profile is not None:
            qs = qs.exclude(pk=self.profile.pk)
        if qs.exists():
            raise forms.ValidationError('Ten numer chip jest już przypisany do innego konta.')
        return chip_number
