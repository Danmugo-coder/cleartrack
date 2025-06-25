from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# ✅ Replaces lambda for default trial end date
def default_trial_end():
    return timezone.now() + timedelta(days=14)

class Plan(models.Model):
    """
    Represents a subscription plan that a user can purchase.
    Includes pricing, duration, and feature details.
    """
    name = models.CharField(
        max_length=50,
        help_text="Name of the plan (e.g., Basic, Pro, Premium)"
    )
    price_monthly = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Monthly price in USD"
    )
    price_yearly = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Yearly price in USD"
    )
    duration_days = models.IntegerField(
        default=30,
        help_text="Duration of the plan in days"
    )
    features = models.TextField(
        blank=True,
        help_text="Optional description or bullet list of features"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_monthly']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/mo or ${self.price_yearly}/yr"


class Subscription(models.Model):
    """
    Tracks a user's active subscription, including expiration and plan details.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        help_text="User tied to this subscription"
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Subscribed plan"
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date when the subscription started"
    )
    end_date = models.DateTimeField(
        help_text="Date when the subscription will expire"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the subscription is currently active"
    )
    trial_ends_at = models.DateTimeField(
        default=default_trial_end,
        help_text="End date for the 14-day free trial"
    )

    class Meta:
        ordering = ['-end_date']
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def has_expired(self):
        return timezone.now() > self.end_date

    def days_remaining(self):
        return max((self.end_date - timezone.now()).days, 0)

    def is_trial_active(self):
        return timezone.now() <= self.trial_ends_at

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"
class Invoice(models.Model):
    """
    Stores invoice records for completed payments.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    billing_type = models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='PayPal')  # or Visa/Card later
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        return f"Invoice #{self.id} - {self.user.username} - {self.amount} USD"

