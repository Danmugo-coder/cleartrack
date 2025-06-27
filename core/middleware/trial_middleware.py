from django.shortcuts import redirect
from django.utils import timezone
from billing.models import Subscription

class TrialCheckMiddleware:
    """
    Restricts access after the trial period ends if the user has not subscribed.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only for authenticated users
        if request.user.is_authenticated and not request.user.is_superuser:
            try:
                subscription = Subscription.objects.get(user=request.user)
                if subscription.has_expired():
                    if not request.path.startswith('/billing/') and not request.path.startswith('/accounts/logout'):
                        return redirect('billing:subscribe')
            except Subscription.DoesNotExist:
                # Redirect if no subscription exists (never subscribed after trial)
                if not request.path.startswith('/billing/') and not request.path.startswith('/accounts/logout'):
                    return redirect('billing:subscribe')

        return self.get_response(request)
