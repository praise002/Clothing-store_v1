from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from apps.common.utils import TestUtil
from apps.shop.models import Product
from apps.cart.cart import Cart
from django.http import JsonResponse


class CartViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = TestUtil.verified_user()
        self.profile = self.user.profile
        self.product = TestUtil.create_product()
        self.client.force_login(self.user)
        self.cart_url = reverse("cart:cart_detail")
        self.add_url = reverse("cart:cart_add", args=[self.product.id])
        self.remove_url = reverse("cart:cart_remove", args=[self.product.id])

    def test_cart_add_product(self):
        response = self.client.post(self.add_url, {"quantity": 1, "override": False})
        
        self.assertRedirects(
            response,
            self.cart_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_cart_remove_product(self):
        self.client.post(self.add_url, {"quantity": 1, "override": False})
        response = self.client.delete(self.remove_url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cart/partials/cart_detail.html")
        
        # non-htmx
        response = self.client.delete(self.remove_url)
        
        self.assertRedirects(
            response,
            self.cart_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        

    def test_cart_detail_view(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cart/cart_detail.html")
