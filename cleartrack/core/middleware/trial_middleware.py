from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings

class TrialCheckMiddleware:
    """
    Blocks users from accessing the platform after their 14-day trial ends.
    Admins and staff are excluded from the restriction.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        exempt_paths = [
            '/accounts/login/', 
            '/accounts/logout/', 
            '/accounts/signup/',
            '/billing/subscribe/',
            '/admin/',  # allow admin login
        ]
        is_exempt = any(request.path.startswith(p) for p in exempt_paths)

        if user.is_authenticated and not user.is_superuser and not is_exempt:
            profile = getattr(user, 'profile', None)
            if profile and profile.trial_start_date:
                days_elapsed = (timezone.now().date() - profile.trial_start_date).days
                if days_elapsed > 14 and not profile.is_paid:
                    return redirect('/billing/subscribe/?trial_expired=1')

        return self.get_response(request)
