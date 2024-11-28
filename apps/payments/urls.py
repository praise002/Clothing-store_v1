from django.urls import path
from apps.payments import webhooks as wh
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/', views.payment_process, name='process'), 
    path('success/', views.payment_success, name='success'), 
    path('canceled/', views.payment_canceled, name='canceled'), 
    path('webhook/', wh.stack_webhook, name='stack-webhook'),
]
