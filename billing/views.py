import paypalrestsdk
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta
from billing.models import Plan, Subscription

# ✅ Configure PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET_KEY,
})


def subscribe(request):
    """
    Display available subscription plans.
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
    User selects payment method (currently PayPal only).
    """
    plan = get_object_or_404(Plan, id=plan_id)
    amount = plan.price_yearly if billing_type == 'yearly' else plan.price_monthly

    return render(request, 'billing/choose_payment_method.html', {
        'plan': plan,
        'billing_type': billing_type,
        'amount': amount
    })


@login_required
def create_paypal_payment(request, plan_id, billing_type):
    """
    Generate a PayPal payment link dynamically.
    """
    plan = get_object_or_404(Plan, id=plan_id)
    amount = plan.price_yearly if billing_type == 'yearly' else plan.price_monthly
    description = f"{plan.name} {'Yearly' if billing_type == 'yearly' else 'Monthly'} Subscription"
    sku = f"{plan.name.lower()}_{billing_type}"

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
        return HttpResponse("⚠️ Approval URL not found.")
    else:
        return HttpResponse(f"❌ Payment failed: {payment.error}")


@login_required
def paypal_return(request):
    """
    Finalize subscription after successful PayPal payment.
    Sends an invoice email.
    """
    try:
        latest_plan = Plan.objects.order_by('-id').first()
        if not latest_plan:
            messages.error(request, "No plan found. Contact support.")
            return redirect("billing:subscribe")

        now = timezone.now()
        new_end = now + timedelta(days=latest_plan.duration_days)

        subscription, _ = Subscription.objects.get_or_create(user=request.user)
        subscription.plan = latest_plan
        subscription.start_date = now
        subscription.end_date = new_end
        subscription.is_active = True
        subscription.trial_ends_at = now
        subscription.save()

        # 📤 Send invoice via email
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
            "",  # Plain text fallback
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            html_message=html_message
        )

        messages.success(request, "✅ Subscription activated and invoice sent.")
        return redirect("dashboard:admin_dashboard")

    except Exception as e:
        messages.error(request, f"❌ Subscription error: {str(e)}")
        return redirect("billing:subscribe")


@login_required
def paypal_cancel(request):
    """
    Handle canceled PayPal payment.
    """
    messages.warning(request, "❌ You canceled the PayPal payment.")
    return redirect("billing:subscribe")
