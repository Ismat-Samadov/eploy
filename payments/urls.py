# payments/urls.py
from django.urls import path
from .views import create_payment, payment_success, payment_error, handle_result

urlpatterns = [
    path('create-payment/', create_payment, name='create_payment'),
    path('success/', payment_success, name='payment_success'),
    path('error/', payment_error, name='payment_error'),
    path('result/', handle_result, name='payment_result'),
]
