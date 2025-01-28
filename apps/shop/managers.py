from django.db import models


class ProductManager(models.Manager):
    def available(self):
        """
        Return products that are in stock and available.
        """
        return self.get_queryset().filter(in_stock__gt=0, is_available=True)
    
    def get_index_objects(self):
        """Objects formatted for indexing"""
        # Filter for available products before converting to dict
        available_products = self.available()
        return [h.dict() for h in available_products]