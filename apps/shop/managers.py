from django.db import models


class ProductManager(models.Manager):
    def get_index_objects(self):
        """Objects formatted for indexing"""
        # Filter for available products before converting to dict
        available_products = self.get_queryset().filter(
            in_stock__gt=0, is_available=True
        )
        return [h.dict() for h in available_products]