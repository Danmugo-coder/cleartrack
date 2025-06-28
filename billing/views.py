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
    """
    Renders the subscription page with available plans.
    """
    trial_expired = request.GET.get('trial_expired') == '1'
    plans = Plan.objects.all().order_by('price_monthly')
    return render(request, 'billing/subscribe.html', {
        'plans': plans,
        'trial_expired': trial_expired
    })

@login_required
def choose_payment_method(request, plan_id, billing_type):
    """
    Page where user picks which payment method to use for the selected plan.
    """
    plan = get_object_or_404(Plan, id=plan_id)

    if billing_type == 'yearly':
        amount = plan.price_yearly
    else:
        amount = plan.price_monthly

    return render(request, 'billing/choose_payment_method.html', {
        'plan': plan,
        'billing_type': billing_type,
        'amount': amount
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
from django.utils import timezone
from billing.models import Subscription
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta

@login_required
def paypal_return(request):
    """
    Called after the user completes PayPal payment.
    This function activates the user's subscription and sends invoice.
    """
    try:
        latest_plan = Plan.objects.order_by('-id').first()

        if not latest_plan:
            messages.error(request, "No plan found. Contact support.")
            return redirect("billing:subscribe")

        now = timezone.now()
        new_end = now + timedelta(days=latest_plan.duration_days)

        subscription, created = Subscription.objects.get_or_create(user=request.user)

        subscription.plan = latest_plan
        subscription.start_date = now
        subscription.end_date = new_end
        subscription.is_active = True
        subscription.trial_ends_at = now  # Trial ends now
        subscription.save()

        # 📤 Email Invoice
        subject = f"Invoice for {latest_plan.name} Subscription"
        recipient = request.user.email
        html_message = render_to_string("billing/invoice_email.html", {
            'user': request.user,
            'plan': latest_plan,
            'amount': latest_plan.price_monthly,
            'date': now,
        })

        send_mail(
            subject,
            "",
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            html_message=html_message
        )

        messages.success(request, "✅ Subscription activated and invoice sent.")
        return redirect("dashboard:admin_dashboard")

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("billing:subscribe")
