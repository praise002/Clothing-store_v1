import json
from django.urls import reverse
import requests
from django.shortcuts import get_object_or_404, redirect, render
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
    print(order)
    amount = order.get_total_cost()

    if request.method == "POST":
        success_url = request.build_absolute_uri(
            reverse("payments:success")
        )  # generate absolute url for the url path
        cancel_url = request.build_absolute_uri(reverse("payments:canceled"))

        # add order items to the paystack checkout session
        for item in order.items.all():
            # metadata to pass additional data that
            # the endpoint doesn't accept naturally.
            metadata = json.dumps(
                {
                    "price_data": {
                        "unit_amount": int(item.price * Decimal("100")),
                        "currency": "usd",
                        "product_data": {
                            "name": item.product.name,
                        },
                        "quantity": item.quantity,
                        "client_reference_id": str(order_id),
                        "cancel_action": cancel_url,
                    }
                }
            )

        # Paystack checkout session data
        session_data = {
            "email": order.customer.user.email,
            "amount": int(amount),
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
                return redirect(redirect_url, code=303)
            except:
                pass
        else:
            return render(request, "payments/process.html", locals())
    else:
        return render(request, "payments/process.html", locals())


def payment_success(request):
    return render(request, "payments/success.html")


def payment_canceled(request):
    return render(request, "payments/canceled.html")
