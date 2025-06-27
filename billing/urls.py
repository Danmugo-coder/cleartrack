from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),

    # PayPal Payment Routes
    path('paypal/create/', views.create_paypal_payment, name='create_paypal_payment'),
    path('paypal-return/', views.paypal_return, name='paypal_return'),
    path('paypal-cancel/', views.paypal_cancel, name='paypal_cancel'),
]
