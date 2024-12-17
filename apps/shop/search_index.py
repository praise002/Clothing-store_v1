import meilisearch
from decouple import config

MEILISEARCH_URL = config("MEILISEARCH_URL")
MEILISEARCH_API_TOKEN = config("MEILISEARCH_API_TOKEN")     

class SearchIndex:
    index = None

    class Indexes:
        """Available indexes"""

        app = "app"

    def __init__(self, index=None):
        self.index = index or self.Indexes.app

    def get_index(self):
        """Retrieve index"""
        client = meilisearch.Client(
            MEILISEARCH_URL, MEILISEARCH_API_TOKEN
        )
        return client.index(self.index)

    def delete_doc(self, doc):
        self.get_index().delete_document(doc)

    def clear_index(self):
        self.get_index().delete_all_documents()


search_index = SearchIndex().get_index()

# TODO: TEST, REMOVE LATER
# Using the functions
search = SearchIndex(index="app")
print(search.get_index())


