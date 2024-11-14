from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models.query import QuerySet
from django.http import Http404
from django.core.paginator import Paginator

from apps.shop.forms import ReviewForm
from apps.shop.utils import get_session_key, sort_products, sort_filter_value

from apps.shop.models import Cart, CartItem, Category, Order, Product, OrderItem

class HomeView(View):
    def get(self, request):
        products = Product.objects.all()[:6]
        categories = Category.objects.all()
        context = {
            "products": products,
            "categories": categories,
        }
        return render(request, 'shop/home.html', context)
    
class ProductListView(ListView): 
    model = Product
    paginate_by = 15
    template_name = "shop/product_list.html"
    context_object_name = "products"

    def get_queryset(self) -> QuerySet[Product]:
        products = Product.objects.prefetch_related("reviews")
        products = sort_products(self.request, products)
        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_filter_value(self.request, context)
        return context

class ProductDetailView(View): 
    def get(self, request, *args, **kwargs):
        try:
            product = Product.objects.select_related("category").prefetch_related("reviews", "reviews__customer").get(slug=kwargs["slug"])
        except Product.DoesNotExist:
            raise Http404("Product does not exist")

        form = ReviewForm()
        context = {
            "product": product,
            "form": form
        }
        return render(request, 'shop/product_detail.html', context)
    
class CategoriesView(ListView):
    model = Category
    template_name = "shop/categories.html"
    context_object_name = "categories"
    
class CategoryProductsView(View):
    def get(self, request, *args, **kwargs):
        category = get_object_or_404(Category, slug=kwargs["slug"])
        products = Product.objects.filter(category=category).prefetch_related("reviews")
        products = sort_products(self.request, products)

        # Pagination config
        paginated = Paginator(products, 15)
        page_number = request.GET.get('page')
        page = paginated.get_page(page_number)
        is_paginated = True if page.paginator.num_pages > 1 else False

        context = {"category": category, "page_obj": page, "is_paginated": is_paginated}
        sort_filter_value(self.request, context)
        return render(request, "shop/category_products.html", context)
    
class CartView(ListView):
    model = Cart
    template_name = "shop/cart.html"
    context_object_name = "orderitems"

    def get_queryset(self) -> QuerySet[OrderItem]:
        request = self.request
        user = request.user
        session_key = get_session_key(request)
        if user.is_authenticated:
            return OrderItem.objects.filter(user_id=user.id)
        else:
            return OrderItem.objects.filter(session_key=session_key)
        
class PlaceOrderView(View):
    def post(self, request, *args, **kwargs):
        cart_items = CartItem.objects.filter(order__customer=request.user.profile)

        if not cart_items.exists():
            # If the cart is empty, redirect back to the cart page
            return redirect("shop:cart")

        # Create a new order associated with the user's profile
        order = Order.objects.create(customer=request.user.profile)

        # Create an OrderItem for each CartItem
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        # Clear the cart items after order is placed
        cart_items.delete()

        # Redirect to a confirmation or order summary page
        return redirect("shop:order_summary", order_id=order.id)
    
class OrderSummaryView(DetailView): 
    model = Order
    template_name = "shop/order_summary.html"
    context_object_name = "order"
    pk_url_kwarg = "order_id"