from decimal import Decimal
from django.conf import settings
from apps.shop.models import Product
import redis


class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.user = request.user if request.user.is_authenticated else None

        self.cart = self.get_cart_from_redis()

    def get_cart_from_redis(self):
        """
        Retrieve the cart from Redis for authenticated users.
        """
        redis_client = redis.StrictRedis(host="localhost", port=6379, db=1)

        # Check if cart exists in Redis using user ID as the key
        cart_key = f"cart:{self.user.id}"
        cart = redis_client.get(cart_key)

        if cart:
            # If cart exists, load it
            return cart
        else:
            # If cart does not exist, create a new one
            return {}

    def save_cart_to_redis(self):
        """
        Save the cart to Redis for persistent storage.
        """
        if self.user:
            redis_client = redis.StrictRedis(host="localhost", port=6379, db=1)
            cart_key = f"cart:{self.user.id}"
            redis_client.set(cart_key, self.cart)

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
            
        self.save()
        
    def save(self):
        """
        Save the cart to Redis.
        """
        self.save_cart_to_redis()

    def get_cart_data(self):
        """
        Get cart data (to display in the UI).
        """
        return self.cart
