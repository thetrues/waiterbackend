from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """User class inherit from django default user model"""

    mobile_phone = models.CharField(max_length=14, null=True, blank=True)
    profile_image = models.ImageField(upload_to="users/", null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.username

    class Meta:
        ordering: set = ("-id",)

    EMAIL_FIELD = "username"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "mobile_phone"]
