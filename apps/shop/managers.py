from django.db import models


class ProductManager(models.Manager):
    def get_index_objects(self):
        """Objects formatted for indexing"""
        return [h.dict() for h in self.get_queryset()]

    def get_filter_attributes(self):
        """A dict of filterable attributes"""
        qs = self.get_queryset()
        return {
            "categories": list(set(qs.values_list("category__name", flat=True))),
            "prices": {
                "min": qs.aggregate(min=models.Min("price"))["min"],
                "max": qs.aggregate(max=models.Min("price"))["max"],
            },
            "availability": list(set(qs.values_list("is_available", flat=True))),
            "stock_status": list(set(qs.filter(in_stock__gt=0).values_list("in_stock", flat=True))),
            "featured": list(set(qs.values_list("featured", flat=True))),
            "flash_deals": list(set(qs.values_list("flash_deals", flat=True))),
        }