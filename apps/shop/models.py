from autoslug import AutoSlugField
from django.db import models
from django.urls import reverse

from apps.profiles.models import Profile
from apps.common.models import BaseModel
from django.utils.translation import gettext_lazy as _
from statistics import mean

from apps.common.validators import validate_file_size


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


class Product(BaseModel):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    description = models.TextField(_("Description"))
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.SET_NULL, null=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(
        upload_to="products/", validators=[validate_file_size]
    )
    in_stock = models.PositiveIntegerField()
    featured = models.BooleanField(default=False)
    flash_deals = models.BooleanField(default=False)

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


class Review(BaseModel):
    RATING_CHOICES = ((5, 5), (4, 4), (3, 3), (2, 2), (1, 1))

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    customer = models.ForeignKey(Profile, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.SmallIntegerField(choices=RATING_CHOICES)


