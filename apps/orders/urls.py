from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.OrderCreate.as_view(), name="order_create"),
    path("created/<str:order_id>/", views.OrderCreated.as_view(), name="order_created"),
]
