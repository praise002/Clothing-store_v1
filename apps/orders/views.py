from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from apps.accounts.mixins import LoginRequiredMixin
import weasyprint
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string
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
        # order = Order.objects.create(customer=profile)

        # Create the order instance but do not save it yet
        order = Order(customer=profile)  # Create an in-memory instance

        # Add coupon details if available
        cart = Cart(request)

        if cart.coupon:
            order.coupon = cart.coupon
            order.discount = cart.coupon.discount

        # Save the order after making all changes
        order.save()

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )

        # Clear the cart
        cart.clear()

        # clear the coupon
        request.session.pop("coupon_id", None)

        # launch asynchronous task
        order_created.delay(order.id)

        # set the order in the session
        request.session["order_id"] = str(order.id)

        # redirect for payment
        return redirect("payments:process")


class OrderCreated(LoginRequiredMixin, View):
    def get(self, request, order_id):
        """
        Display a success page after placing an order.
        """
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        return render(request, "orders/order/created.html", {"order": order})


class OrderHistory(LoginRequiredMixin, View):
    def get(self, request):
        # Fetch orders based on shipping status (Pending, Shipped, Delivered, Canceled)
        status_filter = request.GET.get("shipping_status", "P")
        unpaid_orders = Order.objects.filter(paid=False)

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
                paid=False,
            )

        return render(
            request,
            "orders/order/order_history.html",
            {
                "orders": orders,
                "status_filter": status_filter,
                "unpaid orders": unpaid_orders,
            },
        )


class OrderItemDetailView(LoginRequiredMixin, View):
    def get(self, request, order_item_id):
        # Get the specific order item by ID
        order_item = get_object_or_404(OrderItem, id=order_item_id)

        # Get the product associated with the order item
        product = order_item.product
        context = {
            "product": product,
            "order_item": order_item,
            "quantity": order_item.quantity,  # Quantity last bought
        }
        return render(request, "orders/order/order_item_detail.html", context)


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "admin/orders/order/detail.html", {"order": order})


@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string(
        "orders/order/pdf.html",
        {
            "order": order,
        },
    )
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"filename=order_{order.id}.pdf"
    weasyprint.HTML(string=html).write_pdf(
        response, stylesheets=[weasyprint.CSS(finders.find("assets/css/pdf.css"))]
    )
    return response
