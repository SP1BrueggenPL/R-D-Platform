"""Domain constants ported 1:1 from the original Inno Session Lab tool."""

LINES = [
    'Płatki kukurydziane i wielozbożowe',
    'Granola',
    'Ekstrudaty',
    'Poduszki',
    'Musli',
    'Owsianki',
    'Batony',
]

KATS = [
    'Batony', 'Granola', 'Musli', 'Owsianki', 'Płatki śniadaniowe', 'Ekstrudaty',
    'Poduszki', 'Przekąski słodkie', 'Przekąski wytrawne', 'Czekolada',
    'Wyroby cukiernicze', 'Napój', 'Inne',
]

ROLES = [
    'R&D Manager', 'Technolog R&D', 'Specjalista sensoryki', 'Zakupy / Sourcing',
    'Produkcja / Linia', 'Jakość (QA)', 'Marketing', 'Sales',
]

PTYPES = ['Front opakowania', 'Tył / etykieta', 'Produkt (środek)', 'Detal / przekrój']

NOPE = 'Bez Transferu'

# (key, label, weight) — weights sum to 1.0
CRIT = [
    ('wyglad_ocena', 'Wygląd', 0.10),
    ('zapach', 'Zapach', 0.10),
    ('smak', 'Smak', 0.25),
    ('konsystencja', 'Konsystencja', 0.15),
    ('innowacyjnosc', 'Innowacyjność', 0.15),
    ('transfer', 'Możliwość przeniesienia', 0.25),
]
CRIT_KEYS = [c[0] for c in CRIT]

# (field name, label, unit) — per 100 g
NUTRI = [
    ('energia_kcal', 'Energia', 'kcal'),
    ('tluszcz', 'Tłuszcz', 'g'),
    ('nasycone', 'w tym kwasy nasycone', 'g'),
    ('weglowodany', 'Węglowodany', 'g'),
    ('cukry', 'w tym cukry', 'g'),
    ('blonnik', 'Błonnik', 'g'),
    ('bialko', 'Białko', 'g'),
    ('sol', 'Sól', 'g'),
]
NUTRI_KEYS = [n[0] for n in NUTRI]

TRIAL = {
    'Płatki kukurydziane i wielozbożowe': 'Próba na linii płatków: parametry prażenia i tostowania, grubość płatka po walcowaniu, chrupkość i zachowanie w mleku',
    'Granola': 'Próba na linii granoli: prażenie w piecu taśmowym, dozowanie syropu i dodatków, kruszenie i sitowanie frakcji',
    'Ekstrudaty': 'Próba na ekstruderze: profil temperatur, wilgotność masy, stopień ekspansji, oblewanie i dosuszanie',
    'Poduszki': 'Próba koekstruzji: stabilność nadzienia, proporcja nadzienie do otoczki, szczelność zamknięcia, dosuszanie',
    'Musli': 'Próba w mieszalni suchej: proporcja płatków i dodatków, homogeniczność mieszanki, kontrola pylenia i segregacji frakcji',
    'Owsianki': 'Próba w mieszalni: homogeniczność premiksu, rozpuszczalność i czas zalewania, saszetkowanie i waga porcji',
    'Batony': 'Próba na linii batonów: formowanie masy, oblewanie (walce dociskowe), kontrola wagi sztuki',
}

PLAN_TEMPLATE = [
    (1, 'Brief i benchmark', 'R&D Manager',
     'Karta briefu dla kierunku „{flavour}”, zakup 3–5 produktów referencyjnych, cel sensoryczny i ramy kosztowe dla linii {line}'),
    (2, 'Surowce i dostawcy', 'Zakupy / Sourcing',
     'Zapytania do dostawców o aromaty i dodatki, próbki surowców, wstępny koszt na 100 kg, sprawdzenie statusu clean label'),
    (3, 'Receptury laboratoryjne', 'Technolog R&D',
     '3 warianty receptury w skali laboratoryjnej, dobór poziomu aromatu i słodkości, notatki technologiczne'),
    (4, 'Panel sensoryczny', 'Specjalista sensoryki',
     'Test 5-punktowy (smak, zapach, konsystencja), panel 8–10 osób, porównanie z referencją rynkową, wybór 1–2 wariantów'),
    (5, 'Korekta i kalkulacja', 'Technolog R&D',
     'Poprawa wybranego wariantu, kalkulacja kosztu i wartości odżywczych, projekt deklaracji składu'),
    (6, 'Próba technologiczna', 'Produkcja / Linia', None),  # filled from TRIAL[line]
    (7, 'Shelf-life i specyfikacja', 'Jakość (QA)',
     'Start testu przechowalniczego (0 / 1 / 3 mies.), analizy mikro i fizykochemiczne, projekt specyfikacji i etykiety'),
    (8, 'Gate i przekazanie', 'Marketing',
     'Prezentacja próbek dla Sales i Marketingu, rekomendacja go / no-go, wpis do pipeline NPD dla {product}'),
]
