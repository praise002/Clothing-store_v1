from django.urls import path
# from django.utils.translation import gettext_lazy as _
from . import views

app_name = "shop"

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path("orders/", views.PlaceOrderView.as_view(), name="place_order"),
    path("orders/summary/<int:order_id>/", views.OrderSummaryView.as_view(), name="order_summary"),
]
