from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    email_confirmed = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_status = models.CharField(max_length=50, blank=True, null=True)
    # Add more fields as needed
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class Membership(models.Model):
    name = models.CharField(max_length=50)
    stripe_price_id = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
