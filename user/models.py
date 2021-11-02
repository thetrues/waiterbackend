from django.contrib.auth.models import AbstractUser
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import models


USER_TYPE_CHOICES = (
    ("manager", "Manager"),
    ("bar_waiter", "Bar Waiter"),
    ("bar_cashier", "Bar Cashier"),
    ("restaurant_waiter", "Restaurant Waiter"),
    ("restaurant_cashier", "Restaurant Cashier"),
)


class User(AbstractUser):
    """User class inherit from django default user model"""

    mobile_phone = models.CharField(max_length=14, null=True, blank=True, db_index=True)
    profile_image = models.ImageField(upload_to="users/", null=True, blank=True)
    address = models.TextField(null=True, blank=True, db_index=True)
    user_type = models.CharField(max_length=18, choices=USER_TYPE_CHOICES, db_index=True)

    def __str__(self) -> str:
        return self.username

    class Meta:
        ordering: set = ("-id",)

    EMAIL_FIELD = "username"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "mobile_phone", "user_type"]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
