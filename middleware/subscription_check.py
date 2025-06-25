from django.shortcuts import redirect
from django.utils import timezone
from billing.models import Subscription
from datetime import timedelta

class SubscriptionMiddleware:
    """
    Blocks access if the user has no active subscription or trial expired.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith(('/billing/', '/admin/', '/accounts/logout')):
            try:
                subscription = Subscription.objects.get(user=request.user)

                # Block if trial or subscription has expired
                if subscription.has_expired():
                    return redirect('billing:subscribe')

            except Subscription.DoesNotExist:
                # No subscription record → treat as trial user
                profile = request.user.profile
                trial_days = 14
                trial_start = profile.created_at
                trial_end = trial_start + timedelta(days=trial_days)

                if timezone.now() > trial_end:
                    return redirect('billing:subscribe')

        response = self.get_response(request)
        return response
