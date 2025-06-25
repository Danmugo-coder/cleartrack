from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Plan, Subscription

@receiver(post_save, sender=User)
def assign_trial_plan(sender, instance, created, **kwargs):
    if created:
        # Get or create the Free Trial plan
        trial_plan, _ = Plan.objects.get_or_create(
            name="Free Trial",
            defaults={
                "price": 0.00,
                "duration_days": 14,
                "features": "Access to all features for 14 days."
            }
        )

        # Create a subscription for the user
        Subscription.objects.create(
            user=instance,
            plan=trial_plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=trial_plan.duration_days)
        )
