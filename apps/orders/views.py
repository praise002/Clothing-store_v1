from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from apps.accounts.mixins import LoginRequiredMixin
from apps.cart.cart import Cart
from apps.profiles.models import Profile
from .models import Order, OrderItem
from .tasks import order_created


class OrderCreate(LoginRequiredMixin, View):
    """
    Display the order summary before placing the order.
    """

    def get(self, request):
        user = request.user
        profile = get_object_or_404(Profile, user=user)
        cart = Cart(request)

        # Prepare order summary details
        order_summary = {
            "user": user,
            "profile": profile,
            "cart": cart,
            "total_cost": sum(item["price"] * item["quantity"] for item in cart),
        }

        return render(request, "orders/order/create.html", order_summary)

    def post(self, request):
        """
        Place the order and redirect to a success page.
        """
        # Fetch user and profile
        user = request.user
        profile = get_object_or_404(Profile, user=user)

        # Create the order
        order = Order.objects.create(
            customer=profile, payment_status=Order.PAYMENT_STATUS_PENDING
        )

        # Add items to the order
        cart = Cart(request)
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )

        # Clear the cart
        cart.clear()

        # launch asynchronous task
        order_created.delay(order.id)

        return redirect("orders:order_created", order_id=order.id)


class OrderCreated(LoginRequiredMixin, View):
    def get(self, request, order_id):
        """
        Display a success message after placing an order.
        """
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        return render(request, "orders/order/created.html", {"order": order})


class OrderHistory(LoginRequiredMixin, View):
    def get(self, request):
        # Fetch orders based on shipping status (Pending, Shipped, Delivered, Canceled)
        status_filter = request.GET.get("status", "P")

        if status_filter == "P":
            orders = Order.objects.filter(
                customer__user=request.user,
                shipping_status=Order.SHIPPING_STATUS_PENDING,
            )
        elif status_filter == "S":
            orders = Order.objects.filter(
                customer__user=request.user,
                shipping_status=Order.SHIPPING_STATUS_SHIPPED,
            )
        elif status_filter == "D":
            orders = Order.objects.filter(
                customer__user=request.user,
                shipping_status=Order.SHIPPING_STATUS_DELIVERED,
            )
        else:  
            orders = Order.objects.filter(
                customer__user=request.user,
                shipping_status=Order.SHIPPING_STATUS_CANCELED,
            )

        return render(
            request,
            "orders/order/order_history.html",
            {
                "orders": orders,
                "status_filter": status_filter,
            },
        )
