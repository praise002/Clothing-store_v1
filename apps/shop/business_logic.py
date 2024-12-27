import logging

from apps.shop.models import Product
from apps.shop.search_index import search_index

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_ATTRS = ["name", "description"]

def format_search_str(param):
    """Enclose in quotes if there is a space"""
    return f'"{param}"' if " " in param else param

#  Utility functions for generating fake data and updating index

def setup_attributes():
    """Setup index attrs"""
    search_index.update_searchable_attributes(DEFAULT_SEARCH_ATTRS)


def index_products(docs=None):
    """Index all the products"""
    products = Product.objects.filter(
        in_stock__gt=0, 
        is_available=True
    ).select_related('category')
    docs = docs or [d.dict() for d in products]
    # docs = docs or [d.dict() for d in Product.objects.all()]

    logger.info("indexing...")
    result = search_index.add_documents(docs)

    logger.info("setting up filter & sort attributes...")
    setup_attributes()

    logger.info("done")
    return result


def clear_index():
    search_index.delete_all_documents()