import hmac
import hashlib
import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from apps.coupons.models import CouponUsage
from apps.orders.models import Order
from .tasks import payment_completed

logger = logging.getLogger(__name__)
secret = config("PAYSTACK_TEST_SECRET_KEY")


@csrf_exempt
def stack_webhook(request):
    payload = request.body
    sig_header = request.headers.get("x-paystack-signature")
    if not sig_header:
        return HttpResponse("Missing signature header", status=400)

    try:
        hash = hmac.new(secret.encode("utf-8"), payload, digestmod=hashlib.sha512).hexdigest()
        if hash != sig_header:
            raise ValueError("Invalid signature")

        body = json.loads(payload.decode("utf-8"))
        event = body.get("event")
    except (ValueError, KeyError) as e:
        logger.error("Webhook error: %s", str(e))
        return HttpResponse(status=400)

    if event == "charge.success":
        data = body["data"]
        metadata = data.get("metadata", {})
        order_id = metadata.get("order_id")

        if not order_id:
            return HttpResponse("Order ID not found in metadata", status=400)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return HttpResponse("Order not found", status=404)

        if not order.paid and data["status"] == "success" and data["gateway_response"] == "Successful":
            order.paid = True
            order.shipping_status = Order.SHIPPING_STATUS_PENDING
            order.save()

            if order.coupon:
                CouponUsage.objects.create(profile=order.customer.profile, coupon=order.coupon)

            if order.customer.first_purchase:
                order.customer.first_purchase = False
                order.customer.save()

            payment_completed.delay(order.id)

    return HttpResponse(status=200)
