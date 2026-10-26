"""Registry of R&D processes/modules shown on the platform hub.

To add a new process: build it as its own Django app, wire its URLs into
rdplatform/urls.py, then append one entry here. Nothing else on the hub
page needs to change. `tagline` and `description` are {lang: text} dicts
(pl/en/de/fr); the hub picks the visitor's language.
"""

RD_PROCESSES = [
    {
        'slug': 'inno-session-lab',
        'name': 'Inno Session Lab',
        'tagline': {
            'pl': 'Skanuj — oceniaj — przenoś na własne linie',
            'en': 'Scan — rate — transfer to our own lines',
            'de': 'Scannen — bewerten — auf eigene Linien übertragen',
            'fr': 'Scanner — évaluer — transférer vers nos propres lignes',
        },
        'description': {
            'pl': ('Skanowanie i ocena produktów konkurencji z targów i sesji innowacji, '
                   'oraz plany transferu inspiracji na linie produkcyjne.'),
            'en': ('Scanning and rating competitor products from trade fairs and innovation sessions, '
                   'plus plans for transferring inspiration to production lines.'),
            'de': ('Scannen und Bewerten von Wettbewerbsprodukten von Messen und Innovationssessions '
                   'sowie Pläne zur Übertragung der Inspiration auf Produktionslinien.'),
            'fr': ("Scan et évaluation de produits concurrents issus de salons et de sessions d'innovation, "
                   "ainsi que des plans de transfert de l'inspiration vers les lignes de production."),
        },
        'url_name': 'inno_lab:app',
        'enabled': True,
    },
]
