from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    short_description = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True, help_text='All nums (year-month-day)')
    image = models.ImageField(blank=True, null=True)

    country = models.CharField(max_length=33, blank=True)
    town = models.CharField(max_length=33, blank=True)
    address = models.CharField(max_length=77, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)

    current_loaned_books = models.IntegerField(default=0)
    total_loaned_books = models.IntegerField(default=0)
    total_loaned_days = models.IntegerField(default=0)

    overdue_books = models.IntegerField(default=0)
    total_overdue_books_over_time = models.IntegerField(default=0)
    total_overdue_days = models.IntegerField(default=0)

    user_reputation = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
