from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import LoginRequiredMixin
from apps.coupons.forms import CouponApplyForm
from apps.shop.models import Product
from apps.shop.recommender import Recommender
from .cart import Cart
from .forms import CartAddProductForm


class CartAdd(LoginRequiredMixin, View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        form = CartAddProductForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cart.add(
                product=product,
                quantity=cd["quantity"],
                override_quantity=cd["override"],
            )
        return redirect("cart:cart_detail")


class CartRemove(LoginRequiredMixin, View):
    def delete(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        
        # Prepare the context for the partial template
        for item in cart:
            item["update_quantity_form"] = CartAddProductForm(
                initial={"quantity": item["quantity"], "override": True}
            )
            
        coupon_apply_form = CouponApplyForm()

        r = Recommender()
        cart_products = [item["product"] for item in cart]
        if cart_products:
            recommended_products = r.suggest_products_for(cart_products, max_results=4)
        else:
            recommended_products = []

        if request.htmx:
            return render(
                request, "cart/partials/cart_detail.html", 
                {
                    "cart": cart,
                    "coupon_apply_form": coupon_apply_form,
                    "recommended_products": recommended_products,
                }, 
                status=200
            )
        else:
            return redirect("cart:cart_detail")


class CartDetail(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart(request)
        for item in cart:
            item["update_quantity_form"] = CartAddProductForm(
                initial={"quantity": item["quantity"], "override": True}
            )

        coupon_apply_form = CouponApplyForm()

        r = Recommender()
        cart_products = [item["product"] for item in cart]
        if cart_products:
            recommended_products = r.suggest_products_for(cart_products, max_results=4)
        else:
            recommended_products = []

        return render(
            request,
            "cart/cart_detail.html",
            {
                "cart": cart,
                "coupon_apply_form": coupon_apply_form,
                "recommended_products": recommended_products,
            },
        )
