from django.shortcuts import redirect
from django.utils import timezone

class TrialCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile and hasattr(profile, 'start_date'):
                trial_days = 14
                elapsed_days = (timezone.now().date() - profile.start_date).days
                if elapsed_days > trial_days:
                    return redirect('/billing/subscribe/')
        return self.get_response(request)
