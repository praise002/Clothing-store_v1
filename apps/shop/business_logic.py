import logging

from apps.shop.models import Product
from apps.shop.search_index import search_index

logger = logging.getLogger(__name__)

DEFAULT_FILTER_ATTRS = ["category"]
DEFAULT_SORT_ATTRS = ["price"] # asc or desc will be specified in query params(field:direction)
DEFAULT_SEARCH_ATTRS = ["name", "description"]

def format_search_str(param):
    """Enclose in quotes if there is a space"""
    return f'"{param}"' if " " in param else param


def format_sort_params(query_dict, sort_attrs):
    """Format sort attrs for meilisearch"""
    formatted_sort = []
    for sort_attr in sort_attrs:
        s = query_dict.getlist(sort_attr, None)
        if len(s) > 0:
            formatted_sort.extend(s)
    return formatted_sort

def format_filter_params(query_dict, filter_attrs):
    """
    Formats filter attrs for meilisearch
    Example:
    multiple items -> ["multi = one", "multi = two"],
    one item ->  ["category = 'Value with spaces enclose in quotes'" ]

    https://docs.meilisearch.com/reference/api/search.html#filter
    """
    filters = []
    for filter_attr in filter_attrs:
        filters.append(
            [
                f"{filter_attr} = {format_search_str(f)}"
                for f in query_dict.getlist(filter_attr)
            ]
        )
    return filters

def get_opt_params(query_dict, filter_attrs=None, sort_attrs=None):
    """
    Returns dictionary of formatted search options for meili
    """
    filter_attrs = filter_attrs or DEFAULT_FILTER_ATTRS
    sort_attrs = sort_attrs or DEFAULT_SORT_ATTRS

    opt_params = {}
    opt_params.update({"filter": format_filter_params(query_dict, filter_attrs)})
    opt_params.update({"sort": format_sort_params(query_dict, sort_attrs)})

    # offset
    apply_offset = query_dict.get("apply_offset", False)
    opt_params["offset"] = int(query_dict.get("next_offset", 0)) if apply_offset == 'true' else 0

    return opt_params

#  Utility functions for generating fake data and updating index


def setup_attributes():
    """Setup index attrs"""
    search_index.update_filterable_attributes(DEFAULT_FILTER_ATTRS)
    search_index.update_searchable_attributes(DEFAULT_SEARCH_ATTRS)
    search_index.update_sortable_attributes(DEFAULT_SORT_ATTRS)


def index_products(docs=None):
    """Index all the products"""
    docs = docs or [d.dict() for d in Product.filter(in_stock__gt=0, is_available=True).objects.all()]
    # docs = docs or [d.dict() for d in Product.objects.all()]

    logger.info("indexing...")
    result = search_index.add_documents(docs)

    logger.info("setting up filter & sort attributes...")
    setup_attributes()

    logger.info("done")
    return result


def clear_index():
    search_index.delete_all_documents()