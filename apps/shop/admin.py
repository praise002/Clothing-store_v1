from django.contrib import admin
from django.db.models.aggregates import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse
from . import models


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    autocomplete_fields = ["category"]
    list_display = ["name", "price", "category"]
    list_editable = ["price"]
    list_filter = ["category", "in_stock", "flash_deals"]
    list_per_page = 10
    list_select_related = ["category"]
    search_fields = ["name"]


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "products_count"]
    search_fields = ["name"]

    @admin.display(ordering="products_count")
    def products_count(self, category):
        url = (
            reverse("admin:shop_product_changelist")
            + "?"
            + urlencode({"category__id": str(category.id)})
        )
        return format_html('<a href="{}">{} Products</a>', url, category.products_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_count=Count("products"))



