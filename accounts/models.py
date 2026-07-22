from django.db import models
from django.contrib.auth.models import AbstractUser

from dharm_raksha_sangh.image_utils import face_focused_square, optimize_image_file


class User(AbstractUser):
    """
    Custom user model for the project.

    Inherits all standard Django user fields from AbstractUser:
    username, first_name, last_name, email, password, groups,
    user_permissions, is_staff, is_active, is_superuser,
    last_login, and date_joined.
    """

    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to="members/photos/", blank=True, null=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            self._resize_member_photo()

    def _resize_member_photo(self):
        optimize_image_file(
            self.photo.path,
            fit_size=(700, 700),
            quality=82,
            background="#f8f5ee",
            pre_crop=face_focused_square,
        )
