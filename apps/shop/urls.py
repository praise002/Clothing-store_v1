from django.urls import path

# from django.utils.translation import gettext_lazy as _
from . import views

app_name = "shop"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("products/", views.ProductListView.as_view(), name="products_list"),
    path(
        "products/<slug:slug>/", views.ProductListView.as_view(), name="product_detail"
    ),
    path("categories/", views.CategoriesView.as_view(), name="categories"),
    path(
        "categories/<slug:slug>/products/",
        views.CategoryProductsView.as_view(),
        name="categories_product",
    ),
]
