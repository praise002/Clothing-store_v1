
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('', include('apps.shop.urls', namespace='shop')),
    path('', include('apps.general.urls', namespace='general')),
    path('profiles/', include('apps.profiles.urls', namespace='profiles')),
    path('cart/', include('apps.cart.urls', namespace='cart')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, 
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, 
                          document_root=settings.STATIC_ROOT) 
