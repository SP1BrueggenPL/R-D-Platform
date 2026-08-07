"""Registry of R&D processes/modules shown on the platform hub.

To add a new process: build it as its own Django app, wire its URLs into
rdplatform/urls.py, then append one entry here. Nothing else on the hub
page needs to change.
"""

RD_PROCESSES = [
    {
        'slug': 'inno-session-lab',
        'name': 'Inno Session Lab',
        'tagline': 'Skanuj — oceniaj — przenoś na własne linie',
        'description': (
            'Skanowanie i ocena produktów konkurencji z targów i sesji innowacji, '
            'oraz plany transferu inspiracji na linie produkcyjne.'
        ),
        'url_name': 'inno_lab:app',
        'enabled': True,
    },
]
