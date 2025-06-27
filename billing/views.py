import paypalrestsdk
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from billing.models import Plan

# Configure PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET_KEY,
})

def subscribe(request):
    from billing.models import Plan  # make sure Plan is imported here if not already
    trial_expired = request.GET.get('trial_expired') == '1'
    plans = Plan.objects.all().order_by('price_monthly')
    return render(request, 'billing/subscribe.html', {
        'plans': plans,
        'trial_expired': trial_expired
    })

@login_required
def create_paypal_payment(request, plan_id, billing_type):
    """
    Dynamically create a PayPal payment based on plan and billing type.
    """
    plan = get_object_or_404(Plan, id=plan_id)

    if billing_type == 'yearly':
        amount = plan.price_yearly
        description = f"{plan.name} Yearly Subscription"
        sku = f"{plan.name.lower()}_yearly"
    else:
        amount = plan.price_monthly
        description = f"{plan.name} Monthly Subscription"
        sku = f"{plan.name.lower()}_monthly"

    # Create the PayPal payment
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": settings.PAYPAL_RETURN_URL,
            "cancel_url": settings.PAYPAL_CANCEL_URL,
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": plan.name,
                    "sku": sku,
                    "price": str(amount),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(amount),
                "currency": "USD"
            },
            "description": description
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
        return HttpResponse("⚠️ No approval URL found.")
    else:
        return HttpResponse("❌ Payment failed. " + str(payment.error))

@login_required
def paypal_return(request):
    """
    Called after the user completes PayPal payment.
    """
    return HttpResponse("✅ Payment successful. Subscription activated.")

@login_required
def paypal_cancel(request):
    """
    Called if the user cancels the payment.
    """
    messages.warning(request, "❌ You canceled the PayPal payment. Please try again.")
    return redirect("billing:subscribe")
