from django.db import models


class ProductManager(models.Manager):
    def get_index_objects(self):
        """Objects formatted for indexing"""
        # Filter for available products before converting to dict
        available_products = self.get_queryset().filter(
            in_stock__gt=0, is_available=True
        )
        return [h.dict() for h in available_products]

    def get_filter_attributes(self):
        """A dict of filterable attributes"""
        qs = self.get_queryset()

        # Get min and max prices
        price_stats = qs.aggregate(
            min_price=models.Min("price"), max_price=models.Max("price")
        )
        print(price_stats)

        # Create price ranges
        min_price = price_stats["min_price"]
        max_price = price_stats["max_price"]
        price_step = (max_price - min_price) / 4  # Divide into 4 ranges
        print(price_step)
        return {
            "categories": list(set(qs.values_list("category__name", flat=True))),
            "prices": {
                "ranges": [
                    {
                        "label": f"Under {min_price + price_step:,.2f}",
                        "min": float(min_price),
                        "max": float(min_price + price_step),
                    },
                    {
                        "label": f"{min_price + price_step:,.2f} - {min_price + (2 * price_step):,.2f}",
                        "min": float(min_price + price_step),
                        "max": float(min_price + (2 * price_step)),
                    },
                    {
                        "label": f"{min_price + (2 * price_step):,.2f} - {min_price + (3 * price_step):,.2f}",
                        "min": float(min_price + (2 * price_step)),
                        "max": float(min_price + (3 * price_step)),
                    },
                    {
                        "label": f"Over {min_price + (3 * price_step):,.2f}",
                        "min": float(min_price + (3 * price_step)),
                        "max": float(max_price),
                    },
                ],
                "min": float(min_price),
                "max": float(max_price),
            },
            "stock_level": {
                "low": qs.filter(in_stock__lte=10).exists(),
                # "medium": qs.filter(in_stock__range=(11, 30)).exists()
                "medium": qs.filter(in_stock__gt=10, in_stock__lte=30).exists(),
                "high": qs.filter(in_stock__gt=30).exists(),
            },
        }

    def get_flash_deals(self):
        return self.get_queryset().filter(flash_deals=True)

    def get_featured(self):
        return self.get_queryset().filter(featured=True)
