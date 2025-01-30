import json
from django.urls import reverse
import requests
from django.shortcuts import get_object_or_404, redirect, render
import sweetify
from apps.coupons.models import CouponUsage
from apps.orders.models import Order
from decimal import Decimal
from decouple import config

# create the Paystack instance
api_key = config("PAYSTACK_TEST_SECRET_KEY")
url = config("PAYSTACK_INITIALIZE_PAYMENT_URL")


def payment_process(request):
    # retrieve the order_id we'd set in the djago session ealier
    order_id = request.session.get("order_id")
    order = get_object_or_404(Order, id=order_id)
    amount = order.get_total_cost() * Decimal("100")

    # Check if the order has a coupon applied
    if order.coupon:
        # Check if the coupon has been redeemed
        coupon_usage = CouponUsage.objects.filter(
            profile=order.customer,
            coupon=order.coupon,
        ).exists()

        if coupon_usage:
            # Remove the coupon from the order
            order.coupon = None
            order.discount = 0
            order.save(force_update=True)
            # Update the order total if the coupon affects it
            amount = order.get_total_cost() * Decimal("100")
            # Notify about the coupon removal
            sweetify.info(request, f"Coupon removed from order {order_id} due to prior redemption.")

    if request.method == "POST":
        success_url = request.build_absolute_uri(
            reverse("payments:success")
        )  # generate absolute url for the url path
        cancel_url = request.build_absolute_uri(reverse("payments:canceled"))

        # metadata to pass additional data that
        # the endpoint doesn't accept naturally.

        metadata = json.dumps(
            {
                "order_id": order_id,
                "cancel_action": cancel_url,
                #   "client_reference_id": str(order_id),
            }
        )

        # Paystack checkout session data
        session_data = {
            "email": order.customer.user.email,
            "amount": int(amount),  # amount in cents
            "client_reference_id": str(order_id),
            "callback_url": success_url,
            "metadata": metadata,
        }

        headers = {"authorization": f"Bearer {api_key}"}

        # API request to paystack server
        r = requests.post(url, headers=headers, data=session_data)
        response = r.json()
        if response["status"] == True:
            # redirect to Paystack payment form
            try:
                redirect_url = response["data"]["authorization_url"]
                return redirect(redirect_url)
            except:
                pass
        else:
            return render(request, "payments/process.html", locals())
    else:
        return render(request, "payments/process.html", locals())


def payment_success(request):
    order_id = request.session.get("order_id", None)
    order = get_object_or_404(Order, id=order_id)

    # retrieve the query parameter from the request object
    ref = request.GET.get("reference", "")

    # verify transaction endpoint
    url = f"https://api.paystack.co/transaction/verify/{ref}"

    # set auth headers
    headers = {"authorization": f"Bearer {api_key}"}
    r = requests.get(url, headers=headers)
    res = r.json()
    res = res["data"]

    # verify status before setting payment_ref
    if res["status"] == "success":
        # update order payment reference
        order.payment_ref = ref
        order.save()

    return render(request, "payments/success.html")


def payment_canceled(request):
    return render(request, "payments/canceled.html")
