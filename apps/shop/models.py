from uuid import UUID
from autoslug import AutoSlugField
from django_meili.models import IndexMixin
from django.db import models
from django.urls import reverse

from apps.profiles.models import Profile
from apps.common.models import BaseModel
from django.utils.translation import gettext_lazy as _
from statistics import mean

from apps.common.validators import validate_file_size


class CustomIndexMixin(IndexMixin):
    class MeiliMeta:
        primary_key = "id"

    # def meili_serialize(self):
    #     from json import loads
    #     from django.core.serializers import serialize

    #     # Serialize the model instance to JSON
    #     serialized_model = loads(
    #         serialize(
    #             "json",
    #             [self],
    #             use_natural_foreign_keys=True,
    #             use_natural_primary_keys=True,
    #         )
    #     )[0]

    #     fields = serialized_model["fields"]

    #     # Fix UUID serialization
    #     for field_name, field_value in fields.items():
    #         if isinstance(field_value, UUID):  # Check if the value is a UUID
    #             fields[field_name] = str(field_value)  # Convert UUID to string

    #     # Include primary key if specified in MeiliMeta
    #     if getattr(self.MeiliMeta, "include_pk_in_search", False):
    #         primary_key_value = getattr(self, self.MeiliMeta.primary_key)
    #         if isinstance(primary_key_value, UUID):  # Check if the pk is a UUID
    #             primary_key_value = str(primary_key_value)  # Convert to string
    #         fields[self.MeiliMeta.primary_key] = primary_key_value

    #     return fields


class Category(BaseModel):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    @property
    def get_absolute_url(self):
        return reverse("shop:category_products", args=[str(self.slug)])


# NOTE: USE PERMSSIONS IN ADMIN TO PREVENT ACCIDENTAL DELETION OF PRODUCT


class Product(CustomIndexMixin, BaseModel):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.SET_NULL, null=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", validators=[validate_file_size])
    in_stock = models.PositiveIntegerField()
    featured = models.BooleanField(default=False)
    flash_deals = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def num_of_reviews(self):
        return self.reviews.count()

    @property
    def avg_rating(self):
        reviews = [review.rating for review in self.reviews.all()]
        avg = 0
        if len(reviews) > 0:
            avg = round(mean(list(reviews)))  # Mean
        return avg

    @property
    def get_absolute_url(self):
        return reverse("shop:product_detail", args=[str(self.id), str(self.slug)])

    @property
    def image_url(self):
        return self.image.url

    # @property
    # def image_url(self):
    #     try:
    #         url = self.image.url
    #     except:
    #         url = 'https://res.cloudinary.com/dq0ow9lxw/image/upload/v1732236163/fallback_ssjbcw.png'
    #     return url

    class Meta:
        ordering = ["-created"]

    def meili_data(self):
        data = super().meili_data()
        # Convert UUIDs to strings
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
            if "category" in data and data["category"] is not None:
                data["category"] = str(self.category.name)
        return data

    class MeiliMeta:
        filterable_fields = ("category", "price")
        searchable_fields = ("id", "name", "description")
        displayed_fields = ("id", "name", "description", "price")


class Review(BaseModel):
    RATING_CHOICES = ((5, 5), (4, 4), (3, 3), (2, 2), (1, 1))

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    customer = models.ForeignKey(Profile, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.SmallIntegerField(choices=RATING_CHOICES)

    def __str__(self):
        return f"{self.customer.user.full_name} review on {self.product.name}"


class Wishlist(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name="wishlists", blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.full_name} wishlist"
