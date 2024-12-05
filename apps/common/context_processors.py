from apps.cart.cart import Cart
from apps.orders.models import Order


def utils(request):
    return {"rating_range": range(5)}


def cart(request):
    cart = Cart(request)
    return {"cart_length": len(cart), "cart": cart}
