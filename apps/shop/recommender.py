import redis
from django.conf import settings
from uuid import UUID
from .models import Product

# connect to redis
r = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


class Recommender:
    def get_product_key(self, id):
        return f"product:{id}:purchased_with"

    def products_bought(self, products):
        product_ids = [str(p.id) for p in products]
        print("Product IDs:", product_ids)
        for product_id in product_ids:
            print("Product IDs:", product_id)
            for with_id in product_ids:
                print("With IDs:", with_id)
                # get the other products bought with each product
                if product_id != with_id:
                    # increment score for product purchased together
                    r.zincrby(str(self.get_product_key(product_id)), 1, with_id)

    def suggest_products_for(self, products, max_results=6):
        product_ids = [str(p.id) for p in products]
        if len(products) == 1:
            # only 1 product
            suggestions = r.zrange(
                self.get_product_key(product_ids[0]), 0, -1, desc=True
            )[:max_results]
        else:
            # generate a temporary key
            flat_ids = "".join(id for id in product_ids)  # uuid1uuid2uuid3
            tmp_key = f"tmp_{flat_ids}"  # tmp_uuid1uuid2uuid3
            # multiple products, combine scores of all products
            # store the resulting sorted set in a temporary key
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(tmp_key, keys)
            # remove ids for the products the recommendation is for
            r.zrem(tmp_key, *product_ids)
            # get the product ids by their score, descendant sort
            suggestions = r.zrange(tmp_key, 0, -1, desc=True)[:max_results]
            # remove the temporary key
            r.delete(tmp_key)

        suggested_product_ids = [UUID(id.decode("utf-8")) for id in suggestions]
        # get suggested products and sort by order of appearanc
        suggested_products = list(Product.objects.filter(id__in=suggested_product_ids))
        suggested_products.sort(key=lambda x: suggested_product_ids.index(x.id))
        return suggested_products
