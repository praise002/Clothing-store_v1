from django.urls import path

# from django.utils.translation import gettext_lazy as _
from . import views

app_name = "shop"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("products/", views.ProductListView.as_view(), name="products_list"),
    path(
        "products/<str:id>/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product_detail",
    ),
    path("categories/", views.CategoriesView.as_view(), name="categories"),
    path(
        "categories/<slug:slug>/products/",
        views.CategoryProductsView.as_view(),
        name="category_products",
    ),
    path("wishlist/", views.view_wishlist, name="view_wishlist"),
    path(
        "wishlist/add/<str:product_id>/", views.add_to_wishlist, name="add_to_wishlist"
    ),
    path(
        "wishlist/remove/<str:product_id>/",
        views.remove_from_wishlist,
        name="remove_from_wishlist",
    ),
    
    # path("search/", views.search, name="search"),
    path("preview_product/<str:doc_id>", views.preview_product, name="preview"),
]
