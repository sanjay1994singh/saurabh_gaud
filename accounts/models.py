from pathlib import Path

from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image, ImageOps


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
    photo = models.ImageField(upload_to="members/photos/", blank=True, null=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            self._resize_member_photo()

    def _resize_member_photo(self):
        photo_path = Path(self.photo.path)
        if not photo_path.exists():
            return

        with Image.open(photo_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image = self._face_focused_square(image)
            image_format = "PNG" if photo_path.suffix.lower() == ".png" else "JPEG"
            save_kwargs = {"optimize": True}
            if image_format == "JPEG":
                save_kwargs["quality"] = 88
            image.save(photo_path, image_format, **save_kwargs)

    def _face_focused_square(self, image):
        face_box = self._detect_face_box(image)
        width, height = image.size

        if face_box is not None:
            left, top, face_width, face_height = face_box
            center_x = left + face_width / 2
            center_y = top + face_height / 2
            crop_size = int(max(face_width, face_height) * 2.8)
        else:
            center_x = width / 2
            center_y = height * 0.42
            crop_size = min(width, height)

        crop_size = min(max(crop_size, 1), width, height)
        left = max(0, min(width - crop_size, int(center_x - crop_size / 2)))
        top = max(0, min(height - crop_size, int(center_y - crop_size / 2)))
        image = image.crop((left, top, left + crop_size, top + crop_size))
        return image.resize((700, 700), Image.Resampling.LANCZOS)

    def _detect_face_box(self, image):
        try:
            import cv2
            import numpy as np
        except ImportError:
            return None

        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return None

        return max(faces, key=lambda face: face[2] * face[3])
