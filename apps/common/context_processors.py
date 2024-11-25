from apps.cart.cart import Cart


def utils(request):
    return {"rating_range": range(5)}


def cart(request):
    return {"cart": Cart(request)}
