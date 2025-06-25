from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),

    # Step before actual payment - choose method
    path('choose-payment/<int:plan_id>/<str:billing_type>/', views.choose_payment_method, name='choose_payment_method'),

    # PayPal payment
    path('paypal/create/<int:plan_id>/<str:billing_type>/', views.create_paypal_payment, name='create_paypal_payment'),
    path('paypal-return/', views.paypal_return, name='paypal_return'),
    path('paypal-cancel/', views.paypal_cancel, name='paypal_cancel'),
]
