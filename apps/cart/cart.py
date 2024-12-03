from decimal import Decimal
from django.conf import settings
from apps.coupons.models import Coupon
from apps.shop.models import Product
import redis
import json


class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        # Connect to Redis
        self.redis_client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,  # Ensures data is stored as strings
        )

        # Create a unique key for the cart
        # self.cart_key = (
        #     f"cart_{request.user.id}" if request.user.is_authenticated else None
        # )
        self.cart_key = (
            f"cart_{request.user.id}"
            if request.user.is_authenticated
            else f"cart_guest_{request.session.session_key}"
        )

        # Try to get the cart from Redis
        cart = self.redis_client.get(self.cart_key)

        if cart:
            # Load the cart from Redis if it exists
            self.cart = json.loads(cart)
        else:
            # Create an empty cart if not found
            self.cart = {}
            self.redis_client.set(
                self.cart_key, json.dumps(self.cart)
            )  # Save the empty cart in Redis
            
        # store current applied coupon
        self.coupon_id = request.session.get('coupon_id')

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        # Convert product ID to string (Redis requires string keys)
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}

        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        self.save()

    def save(self):
        """
        Save the cart to Redis.
        """
        self.redis_client.set(self.cart_key, json.dumps(self.cart))

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart.keys()
        # get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]["product"] = product
        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    def clear(self):
        """
        Clear the cart in Redis.
        """
        self.cart = {}  # Reset the cart in memory
        self.redis_client.delete(self.cart_key)
        
    @property 
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None
    
    def get_discount(self):
        if self.coupon:
            return (
                self.coupon.discount / Decimal(100)
            ) * self.get_total_price()
        
        return Decimal(0)
    
    def get_total_price_after_discount(self):
        return self.get_total_price() - self.get_discount()
