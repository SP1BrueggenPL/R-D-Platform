from django import forms

from .constants import CRIT, KATS, LINES, NOPE, NUTRI, PTYPES, ROLES
from .models import PlanStep, Product, ProductPhoto, TransferPlan

SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]


class ProductForm(forms.ModelForm):
    target_lines = forms.MultipleChoiceField(
        choices=[(l, l) for l in LINES] + [(NOPE, NOPE)],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Linie docelowe (albo decyzja o braku transferu)',
    )

    class Meta:
        model = Product
        fields = [
            'name', 'brand', 'category', 'composition', 'allergens', 'claims',
            'whats_new', 'appearance', 'conclusion',
            'energia_kcal', 'tluszcz', 'nasycone', 'weglowodany', 'cukry', 'blonnik', 'bialko', 'sol',
            'wyglad_ocena', 'zapach', 'smak', 'konsystencja', 'innowacyjnosc', 'transfer',
        ]
        labels = {
            'name': 'Nazwa produktu',
            'brand': 'Marka',
            'category': 'Kategoria',
            'composition': 'Skład',
            'allergens': 'Alergeny',
            'claims': 'Deklaracje na opakowaniu',
            'whats_new': 'Co jest nowe lub ciekawe',
            'appearance': 'Wygląd produktu i obserwacje wizualne',
            'conclusion': 'Wniosek z degustacji (co konkretnie chcemy odtworzyć)',
        }
        widgets = {
            'claims': forms.Textarea(attrs={'placeholder': 'high protein, no added sugar…', 'rows': 2}),
            'appearance': forms.Textarea(attrs={'placeholder': 'kształt, barwa, przekrój, sposób oblania, widoczne dodatki', 'rows': 2}),
            'conclusion': forms.Textarea(attrs={'placeholder': 'profil piernikowy z nutą karmelową, kremowa konsystencja bez piaszczystości', 'rows': 2}),
            'whats_new': forms.Textarea(attrs={'rows': 2}),
            'composition': forms.Textarea(attrs={'rows': 3}),
            'allergens': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, label, weight in CRIT:
            self.fields[key] = forms.TypedChoiceField(
                coerce=int, choices=SCORE_CHOICES, initial=3,
                widget=forms.RadioSelect, label=f'{label} (waga {int(weight * 100)}%)',
            )
            self.fields[key].required = True
        if self.instance and self.instance.pk:
            self.fields['target_lines'].initial = self.instance.target_lines

    def clean_target_lines(self):
        values = self.cleaned_data['target_lines']
        if NOPE in values and len(values) > 1:
            values = [NOPE]
        return values

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.target_lines = self.cleaned_data.get('target_lines', [])
        if commit:
            instance.save()
        return instance


class ProductPhotoForm(forms.ModelForm):
    class Meta:
        model = ProductPhoto
        fields = ['image', 'photo_type']
        widgets = {'photo_type': forms.Select(choices=[(t, t) for t in PTYPES])}


ProductPhotoFormSet = forms.modelformset_factory(
    ProductPhoto, form=ProductPhotoForm, extra=6, max_num=6, can_delete=True,
)


class ProductFilterForm(forms.Form):
    DECISION_CHOICES = [
        ('Wszystkie', 'Wszystkie'),
        ('Bez decyzji', 'Bez decyzji'),
        (NOPE, NOPE),
        ('Wybrana linia', 'Wybrana linia'),
    ]
    q = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={'placeholder': 'Szukaj w nazwach i wnioskach'}))
    kat = forms.ChoiceField(required=False, label='', choices=[('Wszystkie', 'Wszystkie')] + [(k, k) for k in KATS])
    decf = forms.ChoiceField(required=False, label='', choices=DECISION_CHOICES)


class NewPlanForm(forms.Form):
    line = forms.ChoiceField(choices=[(l, l) for l in LINES], label='Linia docelowa')
    flavour = forms.CharField(required=False, label='Kierunek do odtworzenia')
    start_date = forms.DateField(required=False, label='Start projektu — data (opcjonalnie)', widget=forms.DateInput(attrs={'type': 'date'}))
    use_template = forms.ChoiceField(
        choices=[('1', 'Szablon 8 kroków'), ('0', 'Pusty — dodam kroki sam')],
        widget=forms.RadioSelect, initial='1', label='',
    )


class PlanEditForm(forms.ModelForm):
    class Meta:
        model = TransferPlan
        fields = ['line', 'start_date', 'progress']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'})}


PROGRESS_CHOICES = [(i, f'{i}%') for i in range(0, 101, 10)]


class PlanStepForm(forms.ModelForm):
    class Meta:
        model = PlanStep
        fields = ['title', 'date', 'tasks', 'role', 'initials', 'done']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'tasks': forms.Textarea(attrs={'rows': 3}),
            'initials': forms.TextInput(attrs={'maxlength': 4, 'placeholder': 'np. AK', 'style': 'text-transform:uppercase'}),
        }


class NewStepForm(forms.Form):
    title = forms.CharField(label='Nazwa kroku')
