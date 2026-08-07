from django import forms


class ChipLoginForm(forms.Form):
    chip_number = forms.CharField(
        label='Numer chip',
        max_length=20,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'inputmode': 'numeric',
            'placeholder': 'np. 21012',
            'autocomplete': 'off',
        }),
    )
