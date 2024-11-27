from apps.cart.cart import Cart


def utils(request):
    return {"rating_range": range(5)}


def cart(request):
    cart = Cart(request)
    return {"cart_length": len(cart)}
