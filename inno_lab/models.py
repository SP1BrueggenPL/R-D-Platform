from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import CRIT, KATS, LINES, NOPE, NUTRI_KEYS, PTYPES, ROLES


def weighted_index(scores: dict) -> float:
    """scores: {crit_key: int 1-5}. Missing keys default to 3, matching the
    original tool's draft default so a half-filled scan still shows a sane
    live index."""
    total = 0.0
    for key, _label, weight in CRIT:
        total += float(scores.get(key) or 3) * weight
    return total


def verdict_for(index) -> dict:
    if index is None:
        return {'text': '—', 'color': '#7885A2'}
    index = float(index)
    if index >= 4:
        return {'text': 'Do transferu', 'color': '#FF4143'}
    if index >= 3:
        return {'text': 'Obserwuj', 'color': '#E2BC54'}
    return {'text': 'Odrzuć', 'color': '#7885A2'}


class Product(models.Model):
    SOURCE_SESJA = 'sesja'
    SOURCE_ARCHIWUM = 'archiwum'
    SOURCE_CHOICES = [(SOURCE_SESJA, 'Sesja'), (SOURCE_ARCHIWUM, 'Archiwum')]

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_SESJA)
    legacy_nr = models.PositiveIntegerField(null=True, blank=True, help_text='Nr z pierwotnego archiwum, jeśli dotyczy.')

    date = models.DateField(null=True, blank=True, verbose_name='Data')
    name = models.CharField(max_length=300, verbose_name='Nazwa produktu')
    brand = models.CharField(max_length=200, blank=True, default='', verbose_name='Marka')
    category = models.CharField(max_length=100, choices=[(k, k) for k in KATS], default='Batony', verbose_name='Kategoria')

    composition = models.TextField(blank=True, default='', verbose_name='Skład')
    allergens = models.TextField(blank=True, default='', verbose_name='Alergeny')
    claims = models.TextField(blank=True, default='', verbose_name='Deklaracje na opakowaniu')
    whats_new = models.TextField(blank=True, default='', verbose_name='Co jest nowe lub ciekawe')
    appearance = models.TextField(blank=True, default='', verbose_name='Wygląd produktu i obserwacje wizualne')
    conclusion = models.TextField(blank=True, default='', verbose_name='Wniosek z degustacji / insight')

    # Nutrition, per 100 g — free text so a literal "?" (unknown) is allowed.
    energia_kcal = models.CharField(max_length=20, blank=True, default='')
    tluszcz = models.CharField(max_length=20, blank=True, default='')
    nasycone = models.CharField(max_length=20, blank=True, default='')
    weglowodany = models.CharField(max_length=20, blank=True, default='')
    cukry = models.CharField(max_length=20, blank=True, default='')
    blonnik = models.CharField(max_length=20, blank=True, default='')
    bialko = models.CharField(max_length=20, blank=True, default='')
    sol = models.CharField(max_length=20, blank=True, default='')

    # Scoring, 1-5 each. Null for archive rows (no per-criterion breakdown).
    wyglad_ocena = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    zapach = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    smak = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    konsystencja = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    innowacyjnosc = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    transfer = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    # Overall weighted score (1.0-5.0). Computed from the six fields above for
    # session entries; entered directly for archive rows ported from the old tool.
    overall_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name='Ocena')

    # Decision: list of chosen LINES, or [NOPE], or [] (no decision yet).
    target_lines = models.JSONField(default=list, blank=True)

    external_url = models.URLField(blank=True, default='', help_text='Link SharePoint do oryginalnego zdjęcia (wpisy archiwalne).')
    external_filename = models.CharField(max_length=300, blank=True, default='', help_text='Oryginalna nazwa pliku, do dopasowania zdjęć z SharePoint.')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-overall_score', '-created_at']
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkty'

    def __str__(self):
        return self.name

    @property
    def scores(self) -> dict:
        return {key: getattr(self, key) for key, _l, _w in CRIT}

    @property
    def has_full_scores(self) -> bool:
        return all(getattr(self, key) is not None for key, _l, _w in CRIT)

    def recompute_score(self):
        if self.has_full_scores:
            self.overall_score = Decimal(str(weighted_index(self.scores))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        if self.source == self.SOURCE_SESJA:
            self.recompute_score()
        super().save(*args, **kwargs)

    @property
    def verdict(self) -> dict:
        return verdict_for(self.overall_score)

    @property
    def is_no_transfer(self) -> bool:
        return self.target_lines == [NOPE]

    @property
    def has_plan(self) -> bool:
        return hasattr(self, 'plan')

    @property
    def is_deletable(self) -> bool:
        return self.source == self.SOURCE_SESJA


class ProductPhoto(models.Model):
    product = models.ForeignKey(Product, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='inno_lab/photos/%Y/%m/')
    photo_type = models.CharField(max_length=40, choices=[(t, t) for t in PTYPES], default=PTYPES[0])
    original_filename = models.CharField(max_length=300, blank=True, default='')
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Zdjęcie produktu'
        verbose_name_plural = 'Zdjęcia produktu'

    def __str__(self):
        return f'{self.product.name} — {self.photo_type}'


class TransferPlan(models.Model):
    product = models.OneToOneField(Product, related_name='plan', on_delete=models.CASCADE)
    line = models.CharField(max_length=100, choices=[(l, l) for l in LINES], verbose_name='Linia docelowa')
    flavour = models.CharField(max_length=300, blank=True, default='', verbose_name='Kierunek do odtworzenia')
    start_date = models.DateField(null=True, blank=True, verbose_name='Start projektu')
    progress = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)], verbose_name='Postęp projektu (%)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Action plan'
        verbose_name_plural = 'Action plany'

    def __str__(self):
        return f'{self.product.name} → {self.line}'

    def recompute_progress_from_steps(self):
        steps = list(self.steps.all())
        if not steps:
            return self.progress
        done = sum(1 for s in steps if s.done)
        self.progress = round(done / len(steps) * 100)
        return self.progress


class PlanStep(models.Model):
    plan = models.ForeignKey(TransferPlan, related_name='steps', on_delete=models.CASCADE)
    nr = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=300)
    role = models.CharField(max_length=60, choices=[(r, r) for r in ROLES])
    tasks = models.TextField(blank=True, default='')
    initials = models.CharField(max_length=4, blank=True, default='', help_text='Tylko inicjały — bez pełnych danych osobowych.')
    done = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['nr']
        verbose_name = 'Krok planu'
        verbose_name_plural = 'Kroki planu'

    def __str__(self):
        return f'{self.plan_id} · krok {self.nr} · {self.title}'


class LegacyStorageEntry(models.Model):
    """Backs the original standalone tool's `window.storage.get/set` calls
    (see views.legacy_storage) so its own built-in shared-database/sync
    logic (pull every 12s, merge on push) persists to the real DB instead
    of being lost on browser close, deploy, or restart. Just two rows in
    practice: 'inno:core' (items/plans/decisions) and 'inno:imgs' (photos)."""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wpis pamięci (narzędzie oryginalne)'
        verbose_name_plural = 'Wpisy pamięci (narzędzie oryginalne)'

    def __str__(self):
        return self.key
