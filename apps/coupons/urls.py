from django.urls import path
from . import views

app_name = "coupons"

urlpatterns = [
    path("apply/", views.CouponApply.as_view(), name="apply"),
]
