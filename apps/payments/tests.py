from django.test import TestCase, Client
from django.urls import reverse
from apps.common.utils import TestUtil
from apps.shop.models import Product
from apps.cart.cart import Cart
from apps.orders.models import Delivery, Order


from unittest.mock import patch


class PaymentProcessTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = TestUtil.verified_user()
        self.profile = self.user.profile
        self.delivery = Delivery.objects.create()
        self.order = Order.objects.create(customer=self.profile, delivery=self.delivery)
        self.client.force_login(self.user)
        self.payment_url = reverse("payments:process")
        self.success_url = reverse("payments:success")
        self.cancel_url = reverse("payments:canceled")

    @patch("requests.post")
    def test_payment_process_post(self, mock_post):
        mock_post.return_value.json.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/test-url"},
        }
        session = self.client.session
        session["order_id"] = str(self.order.id)
        session.save()
        response = self.client.post(self.payment_url)
        
        self.assertEqual(response.status_code, 302)

    @patch("requests.get")
    def test_payment_success(self, mock_get):
        mock_get.return_value.json.return_value = {"data": {"status": "success"}}
        session = self.client.session
        session["order_id"] = str(self.order.id)
        session.save()
        response = self.client.get(self.success_url, {"reference": "test-ref"})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payments/success.html")

    def test_payment_canceled(self):
        response = self.client.get(self.cancel_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payments/canceled.html")


