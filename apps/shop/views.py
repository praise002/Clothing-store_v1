from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from apps.shop.search_index import search_index
from apps.shop.forms import ReviewForm
from apps.shop.recommender import Recommender
from apps.shop.utils import sort_products, sort_filter_value

from apps.shop.models import Category, Product, Wishlist

from apps.cart.forms import CartAddProductForm


class HomeView(View):
    def get(self, request):
        products = Product.objects.filter(in_stock__gt=0, is_available=True).all()[:6]
        categories = Category.objects.all()
        context = {
            "products": products,
            "categories": categories,
        }
        return render(request, "shop/home.html", context)


class ProductListView(ListView):
    model = Product
    paginate_by = 15
    template_name = "shop/product_list.html"
    context_object_name = "products"

    def get_queryset(self) -> QuerySet[Product]:
        products = Product.objects.filter(
            in_stock__gt=0, is_available=True
        ).prefetch_related("reviews")

        # Handle search query
        query = self.request.GET.get("q")
        
        if query:
            results = search_index.search(query=query)
            return results.get("hits", [])  # returns matching result or empty list

        products = sort_products(self.request, products)
        return products

    def get_template_names(self):
        if self.request.htmx:
            return ["shop/htmx/product_list_partial.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_filter_value(self.request, context)
        return context


class ProductDetailView(View):
    def get(self, request, *args, **kwargs):
        try:
            product = (
                Product.objects.select_related("category")
                .prefetch_related("reviews", "reviews__customer")
                .get(
                    id=kwargs.get("id"),
                    slug=kwargs.get("slug"),
                    in_stock__gt=0,
                    is_available=True,
                )
            )
        except Product.DoesNotExist:
            raise Http404("Product does not exist")

        cart_product_form = CartAddProductForm()
        form = ReviewForm()

        r = Recommender()
        recommended_products = r.suggest_products_for([product], 4)
        
        order_item = None
        has_reviewed = False
        
        # check if the product has been delivered
        if request.user.is_authenticated:
            order_item = product.order_items.filter(
                order__customer=request.user.profile, order__shipping_status="D"
            ).values_list(
                "product_id", flat=True
            )  # List of product IDs

            # Check if user has already reviewed

            has_reviewed = product.reviews.filter(customer=request.user.profile).exists()

        context = {
            "product": product,
            "form": form,
            "cart_product_form": cart_product_form,
            "recommended_products": recommended_products,
            "order_item": order_item,
            "has_reviewed": has_reviewed,
        }
        
        template_name = "shop/product_detail.html"
        # Use a single template for both HTMX and non-HTMX requests
        if request.htmx:
            return render(request, template_name, context)

        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=kwargs["id"])
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.customer = request.user.profile
            review.text = form.cleaned_data["text"]
            review.rating = form.cleaned_data["rating"]
            review.save()
            response_data = {
                "success": True,
                "review": {
                    "text": review.text,
                    "rating": review.rating,
                    "customer": review.customer.user.full_name,
                },
            }

            return JsonResponse(response_data)

        response_data = {"success": False, "errors": form.errors}
        return JsonResponse(response_data)


class CategoriesView(ListView):
    model = Category
    template_name = "shop/categories.html"
    context_object_name = "categories"


class CategoryProductsView(View):
    def get(self, request, *args, **kwargs):
        category = get_object_or_404(Category, slug=kwargs["slug"])
        products = Product.objects.filter(
            category=category, in_stock__gt=0, is_available=True
        ).prefetch_related("reviews")
        products = sort_products(self.request, products)

        # Pagination config
        paginated = Paginator(products, 15)
        page_number = request.GET.get("page")
        page = paginated.get_page(page_number)
        is_paginated = True if page.paginator.num_pages > 1 else False

        context = {"category": category, "page_obj": page, "is_paginated": is_paginated}
        sort_filter_value(self.request, context)
        return render(request, "shop/category_products.html", context)


@login_required
def view_wishlist(request):
    wishlist, _ = Wishlist.objects.get_or_create(profile=request.user.profile)
    return render(request, "shop/wishlist.html", {"wishlist": wishlist})


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # if wishlist has been created, get it, else create it
    wishlist, _ = Wishlist.objects.get_or_create(profile=request.user.profile)
    wishlist.products.add(product)
    return redirect("shop:view_wishlist")


@login_required
@require_http_methods(["DELETE"])
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, profile=request.user.profile)
    wishlist.products.remove(product)

    # To support htmx and standard http request
    if request.headers.get("HX-Request"):
        return HttpResponse(status=200)  # or return HttpResponse('')
    else:
        return redirect("shop:view_wishlist")


# TODO: DO FOR CART

# TODO: FOR TEST, REMOVE LATER
# products = Product.objects.get_filter_attributes()
# print(products)
# print(Product.objects.get_flash_deals())
# print(Product.objects.get_featured())
# print(Product.objects.get_index_objects())
