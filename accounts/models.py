from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.models import Department
from datetime import timedelta

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('user', 'User'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='staff')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_landlord = models.BooleanField(default=False, help_text="Check if this user is a landlord/landlady")
    signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    auto_sign = models.BooleanField(default=False, help_text="Enable automatic signing of all assigned fields")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    trial_started_at = models.DateTimeField(default=timezone.now)
    is_trial_locked = models.BooleanField(default=False)

    def has_trial_expired(self):
        """Check if trial has passed 14 days."""
        return timezone.now() > self.trial_started_at + timedelta(days=14)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
