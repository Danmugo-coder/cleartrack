from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from billing.models import Plan, Subscription
from datetime import timedelta

@receiver(post_save, sender=User)
def create_trial_subscription(sender, instance, created, **kwargs):
    if created:
        try:
            trial_plan = Plan.objects.filter(name__iexact='Basic').first()
            if trial_plan:
                Subscription.objects.create(
                    user=instance,
                    plan=trial_plan,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=14),
                    is_active=True
                )
        except Exception as e:
            print(f"Error creating trial subscription: {e}")
