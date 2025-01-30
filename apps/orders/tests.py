from django.test import TestCase, Client
from django.urls import reverse

from apps.common.utils import TestUtil

from apps.orders.models import Order, OrderItem, Delivery

from unittest.mock import patch


class OrderViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = TestUtil.verified_user()
        self.admin_user = TestUtil.admin_user()
        self.profile = self.user.profile
        self.product = TestUtil.create_product()
        self.delivery = Delivery.objects.create()
        self.order = Order.objects.create(customer=self.profile, delivery=self.delivery)
        self.client.force_login(self.user)

    def test_order_create_get(self):
        response = self.client.get(reverse("orders:order_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/order/create.html")

    @patch("apps.orders.tasks.order_created.delay")
    def test_order_create_post(self, mock_task):
        response = self.client.post(reverse("orders:order_create"))

        self.assertRedirects(
            response,
            reverse("payments:process"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        order = Order.objects.first()
        self.assertEqual(order.customer, self.profile)
        self.assertEqual(order.delivery_fee, self.delivery.fee)
        mock_task.assert_called_once_with(order.id)

    def test_order_created_get(self):
        response = self.client.get(
            reverse("orders:order_created", args=[self.order.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/order/created.html")

    def test_order_history_get(self):
        Order.objects.create(
            customer=self.profile, shipping_status=Order.SHIPPING_STATUS_PENDING
        )

        response = self.client.get(reverse("orders:order_history"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/order/order_history.html")
        # print(response.context["orders"])

    def test_order_item_detail_get(self):
        order_item = OrderItem.objects.create(
            order=self.order, product=self.product, price=50
        )
        response = self.client.get(
            reverse("orders:order_item_detail", args=[order_item.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/order/order_item_detail.html")

    def test_admin_order_detail(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("orders:admin_order_detail", args=[self.order.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/orders/order/detail.html")

    def test_admin_order_pdf(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("orders:admin_order_pdf", args=[self.order.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
