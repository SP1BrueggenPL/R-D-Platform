import datetime
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from inno_lab.constants import KATS
from inno_lab.models import Product

SEED_FILE = Path(__file__).resolve().parent.parent.parent / 'seed_data' / 'seed_products.json'


def parse_date(raw):
    if not raw:
        return None
    for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


class Command(BaseCommand):
    help = 'Load the historical Inno Session Lab archive (60 products) as read-only seed data.'

    def handle(self, *args, **options):
        with open(SEED_FILE, encoding='utf-8') as f:
            seed = json.load(f)

        created = 0
        for entry in seed:
            if Product.objects.filter(source=Product.SOURCE_ARCHIWUM, legacy_nr=entry['nr']).exists():
                continue
            category = entry.get('kat') if entry.get('kat') in KATS else 'Inne'
            date_val = parse_date(entry.get('data'))
            Product.objects.create(
                source=Product.SOURCE_ARCHIWUM,
                legacy_nr=entry['nr'],
                date=date_val,
                name=entry.get('nazwa', ''),
                category=category,
                whats_new=entry.get('nowe', ''),
                conclusion=entry.get('insight', ''),
                overall_score=entry.get('ocena'),
                external_filename=entry.get('file', ''),
                external_url=entry.get('url', ''),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Wczytano {created} nowych wpisów archiwalnych (pominięto {len(seed) - created} już istniejących).'))
