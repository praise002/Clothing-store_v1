from django.test import TestCase

from django.urls import reverse
from apps.common.utils import TestUtil
from apps.shop.models import Product, Category, Wishlist


class HomeViewTest(TestCase):
    def setUp(self):
        TestUtil.create_product_with_category()
        self.url = reverse("shop:home")

    def test_home_view_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop/home.html")
        self.assertIn("products", response.context)
        self.assertIn("categories", response.context)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.url = reverse("shop:products_list")
        TestUtil.create_product()

    def test_product_list_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_pagination(self):
        response = self.client.get(self.url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("products", response.context)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.product = TestUtil.create_product_with_category()
        self.url = reverse(
            "shop:product_detail",
            kwargs={"id": self.product.id, "slug": self.product.slug},
        )
        self.user = TestUtil.verified_user()

    def test_product_detail_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # invalid uuid
        url = reverse("shop:product_detail", kwargs={"id": 999, "slug": "invalid"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # not found
        url = reverse(
            "shop:product_detail",
            kwargs={"id": "a998167d-794a-40b9-98e2-7c382d825851", "slug": "invalid"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class WishlistViewTest(TestCase):
    def setUp(self):
        self.user = TestUtil.verified_user()
        self.product = TestUtil.create_product_with_category()
        self.add_wishlist_url = reverse("shop:add_to_wishlist", args=[self.product.id])
        self.view_wishlist_url = reverse("shop:view_wishlist")
        self.remove_wishlist_url = reverse("shop:remove_from_wishlist", args=[self.product.id])

    def test_add_to_wishlist(self):
        self.client.force_login(self.user)
        response = self.client.post(self.add_wishlist_url)
        self.assertRedirects(
            response,
            self.view_wishlist_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.assertTrue(
            self.user.profile.wishlist.products.filter(id=self.product.id).exists()
        )

    def test_remove_from_wishlist(self):
        self.client.force_login(self.user)
        wishlist, _ = Wishlist.objects.get_or_create(profile=self.user.profile)
        wishlist.products.add(self.product)
        response = self.client.delete(self.remove_wishlist_url)
        self.assertFalse(wishlist.products.exists())
        

class CategoriesViewTest(TestCase):
    def setUp(self):
        self.category = TestUtil.create_category()
        self.product = TestUtil.create_product_with_category()

    def test_categories_get(self):
        response = self.client.get(reverse("shop:categories"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.category, response.context["categories"])
        
    def test_category_product_get(self):
        response = self.client.get(reverse("shop:category_products", args=[self.product.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.category, response.context["category"])
