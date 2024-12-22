from django.core.management.base import BaseCommand
from apps.shop.business_logic import setup_attributes, index_products

class Command(BaseCommand):
    help = 'Setup Meilisearch index and attributes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up Meilisearch index...')
        setup_attributes()
        index_products()
        self.stdout.write(self.style.SUCCESS('Successfully set up Meilisearch index'))