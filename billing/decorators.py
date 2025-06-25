from django.shortcuts import redirect
from billing.models import Subscription
from django.utils import timezone

def subscription_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        try:
            subscription = Subscription.objects.get(user=request.user)
            now = timezone.now()

            # Trial expired and subscription inactive
            if subscription.trial_ends_at < now and not subscription.is_active:
                return redirect('/billing/subscribe/?trial_expired=1')

        except Subscription.DoesNotExist:
            # No subscription at all
            return redirect('/billing/subscribe/?trial_expired=1')

        return view_func(request, *args, **kwargs)
    return _wrapped_view
