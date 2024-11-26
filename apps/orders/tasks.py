from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Order


@shared_task
def order_created(order_id):
    """
    Task to send an e-mail notification when an order is
    successfully created.
    """
    order = Order.objects.get(id=order_id)
    user = order.customer.user
    subject = f"Order nr. {order.id}"
    context = {
        "order": order,
    }
    message = render_to_string("orders/emails/order_placed.html", context)
    email_message = EmailMessage(subject=subject, body=message, to=[user.email])
    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)
