from django.db import models

from apps.common.models import BaseModel
from apps.profiles.models import Profile
from apps.shop.models import Product


class Order(BaseModel):

    # Shipping status
    SHIPPING_STATUS_PENDING = "P"
    SHIPPING_STATUS_SHIPPED = "S"
    SHIPPING_STATUS_DELIVERED = "D"
    SHIPPING_STATUS_CANCELED = "C"

    SHIPPING_STATUS_CHOICES = [
        (SHIPPING_STATUS_PENDING, "PENDING"),
        (SHIPPING_STATUS_SHIPPED, "SHIPPED"),
        (SHIPPING_STATUS_DELIVERED, "DELIVERED"),
        (SHIPPING_STATUS_CANCELED, "CANCELED"),
    ]

    customer = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name="orders"
    )
    paid = models.BooleanField(default=False)
    shipping_status = models.CharField(
        max_length=1, choices=SHIPPING_STATUS_CHOICES, blank=True
    )
    placed_at = models.DateTimeField(auto_now_add=True)
    payment_ref = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ["-placed_at"]
        indexes = [
            models.Index(fields=["-placed_at"]),
        ]

    def __str__(self):
        return f"Order {self.id} by {self.customer.user.full_name}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.PROTECT)
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_cost(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} of {self.product} in order {self.order.id}"
