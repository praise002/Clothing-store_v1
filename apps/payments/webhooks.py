import hmac
import hashlib
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from apps.coupons.models import CouponUsage
from apps.orders.models import Order
from apps.shop.models import Product
from apps.shop.recommender import Recommender
from .tasks import payment_completed

secret = config("PAYSTACK_TEST_SECRET_KEY")


@csrf_exempt
def stack_webhook(request):
    payload = request.body
    sig_header = request.headers.get("x-paystack-signature")
    body = None
    event = None

    try:
        # sign the payload with `HMAC SHA512`
        hash = hmac.new(
            secret.encode("utf-8"), payload, digestmod=hashlib.sha512
        ).hexdigest()

        # compare our signature with paystacks signature
        if hash == sig_header:
            # if signature matches,
            # proceed to retrive event status from payload
            body_unicode = payload.decode("utf-8")
            body = json.loads(body_unicode)
            # event status
            event = body["event"]
        else:
            raise Exception
    except Exception as e:
        # Invalid payload
        return HttpResponse(status=400)
    except KeyError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except:
        # Invalid signature
        return HttpResponse(status=400)

    if event == "charge.success":
        # if event status equals 'charge.success'
        # get the data and the `payment_id`
        # we'd set in the metadata ealier
        data, order_id = body["data"], body["data"]["metadata"]["order_id"]

        # validate status and gateway_response
        if (data["status"] == "success") and (data["gateway_response"] == "Successful"):
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)
            
            # mark payment as paid
            order.paid = True
            order.shipping_status = Order.SHIPPING_STATUS_PENDING
            order.save(force_update=True)
            print("PAID")

            if order.coupon:
                CouponUsage.objects.create(
                    profile=order.customer.profile, coupon=order.coupon
                )
                
            # save items bought for product recommendations
            product_ids = order.items.values_list('product_id')
            products = Product.objects.filter(id__in=product_ids)
            r = Recommender()
            r.products_bought(products)
            
            payment_completed.delay(order.id)

    return HttpResponse(status=200)


