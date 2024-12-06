from apps.cart.cart import Cart

FIRST_PURCHASE_DISCOUNT = 10 #TODO: MOVE TO A CENTRAL UTILITY FN LATER

def utils(request):
    return {"rating_range": range(5)}


def cart(request):
    cart = Cart(request)
    return {"cart_length": len(cart), "cart": cart}

def discount(request):
    return {"first_purchase_discount": FIRST_PURCHASE_DISCOUNT}
