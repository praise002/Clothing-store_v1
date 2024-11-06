from django.urls import path
# from django.utils.translation import gettext_lazy as _
from . import views

app_name = "shop"

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
]