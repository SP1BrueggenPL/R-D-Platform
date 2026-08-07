"""AI features for Inno Session Lab: reading a label from photos, and
detailing a transfer-plan schedule.

Both are OPTIONAL conveniences — every field they touch stays fully editable
by hand, and the app works completely without AI configured (matching the
graceful-degradation behaviour of the original tool). Wired for Azure OpenAI
GPT-4o; disabled until AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY are set
(see settings.AI_FEATURES_ENABLED).
"""
import json

from django.conf import settings

from ..constants import KATS, NUTRI_KEYS


class AIUnavailable(Exception):
    """Raised whenever an AI call cannot be made or parsed — callers should
    catch this and fall back to manual entry, never let it bubble up as a
    500."""


def _client():
    if not settings.AI_FEATURES_ENABLED:
        raise AIUnavailable('Funkcje AI nie są jeszcze skonfigurowane (brak danych Azure OpenAI).')
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise AIUnavailable('Pakiet "openai" nie jest zainstalowany.') from exc
    return AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith('```'):
        text = text.strip('`')
        if text.lower().startswith('json'):
            text = text[4:]
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end == -1:
        raise AIUnavailable('Odpowiedź modelu nie zawiera poprawnego JSON.')
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise AIUnavailable(f'Nie udało się odczytać odpowiedzi modelu: {exc}') from exc


LABEL_PROMPT = (
    'Jesteś technologiem żywności. Przeanalizuj wszystkie powyższe zdjęcia JEDNEGO produktu '
    'spożywczego — każde jest opisane rolą (front opakowania, tył z etykietą, produkt wyjęty '
    'z opakowania, detal).\n'
    'Nazwę, markę i deklaracje odczytaj z frontu. Skład, alergeny i tabelę wartości odżywczych '
    'odczytaj z tyłu / etykiety. Wygląd, barwę, kształt, przekrój i domniemaną konsystencję '
    'opisz na podstawie zdjęcia produktu.\n'
    'Zwróć WYŁĄCZNIE JSON bez komentarza:\n'
    '{{"nazwa":"","marka":"","kat":"jedna z: {kats}","sklad":"pełna lista składników",'
    '"alergeny":"","claims":"deklaracje z opakowania",'
    '"nowe":"co jest nowe lub ciekawe z perspektywy R&D, 1 zdanie",'
    '"wyglad":"opis wyglądu i konsystencji ze zdjęcia produktu, 1-2 zdania",'
    '"nutri":{{"energia_kcal":"","tluszcz":"","nasycone":"","weglowodany":"","cukry":"",'
    '"blonnik":"","bialko":"","sol":""}}}}\n'
    'Wartości odżywcze na 100 g, liczby bez jednostek. Jeżeli czegoś nie widać na żadnym '
    'zdjęciu, wpisz "?" — nie zgaduj.\n'
    'Pola opisowe napisz w jezyku: polski.'
)

PHOTO_LABEL_BY_TYPE = {
    'Front opakowania': 'Zdjęcie — front opakowania:',
    'Tył / etykieta': 'Zdjęcie — tył z etykietą:',
    'Produkt (środek)': 'Zdjęcie — produkt wyjęty z opakowania:',
    'Detal / przekrój': 'Zdjęcie — detal / przekrój:',
}


def read_label(photos) -> dict:
    """photos: iterable of ProductPhoto instances (must have .image and
    .photo_type). Returns a dict matching the LABEL_PROMPT schema above."""
    if not photos:
        raise AIUnavailable('Najpierw wgraj co najmniej jedno zdjęcie.')

    import base64
    content = []
    for photo in photos:
        content.append({'type': 'text', 'text': PHOTO_LABEL_BY_TYPE.get(photo.photo_type, 'Zdjęcie:')})
        with photo.image.open('rb') as fh:
            data = base64.b64encode(fh.read()).decode('ascii')
        media_type = 'image/jpeg' if str(photo.image.name).lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        content.append({'type': 'image_url', 'image_url': {'url': f'data:{media_type};base64,{data}'}})
    content.append({'type': 'text', 'text': LABEL_PROMPT.format(kats=' | '.join(KATS))})

    client = _client()
    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        max_tokens=1500,
        messages=[{'role': 'user', 'content': content}],
    )
    data = _extract_json(response.choices[0].message.content)

    result = {}
    for field in ('nazwa', 'marka', 'sklad', 'alergeny', 'claims', 'nowe', 'wyglad'):
        if data.get(field):
            result[field] = data[field]
    if data.get('kat') in KATS:
        result['kat'] = data['kat']
    nutri = data.get('nutri') or {}
    result['nutri'] = {k: nutri[k] for k in NUTRI_KEYS if nutri.get(k)}
    return result


ENRICH_PROMPT = (
    'Jesteś kierownikiem projektów NPD w firmie produkującej batony, granolę, owsianki i '
    'ekstrudaty zbożowe.\n'
    'Produkt inspiracja: "{product}". Kierunek do odtworzenia: "{flavour}". Linia docelowa: "{line}".\n'
    'Uszczegółowij {n}-tygodniowy harmonogram. Zwróć WYŁĄCZNIE JSON: '
    '{{"weeks":[{{"nr":1,"title":"","tasks":""}}, ... {n} pozycji]}}\n'
    'Zadania konkretne i technologiczne (poziomy dodatków, parametry procesu, rodzaj testu), '
    'w jezyku: polski, max 220 znaków na krok. Bez nazw osób.'
)


def enrich_plan(plan) -> dict:
    """plan: TransferPlan instance. Returns {"weeks": [{"nr", "title", "tasks"}, ...]}."""
    client = _client()
    steps = list(plan.steps.all())
    prompt = ENRICH_PROMPT.format(
        product=plan.product.name, flavour=plan.flavour or plan.product.name,
        line=plan.line, n=len(steps) or 8,
    )
    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        max_tokens=1000,
        messages=[{'role': 'user', 'content': prompt}],
    )
    data = _extract_json(response.choices[0].message.content)
    weeks = data.get('weeks')
    if not isinstance(weeks, list):
        raise AIUnavailable('Odpowiedź modelu nie zawiera listy "weeks".')
    return {'weeks': weeks}
