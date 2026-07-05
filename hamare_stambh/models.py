from pathlib import Path

from django.db import models
from django.urls import reverse
from PIL import Image, ImageOps


class HamareStambh(models.Model):
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=150, blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to="hamare_stambh/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")
        verbose_name = "hamare stambh"
        verbose_name_plural = "hamare stambh"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("hamare_stambh:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            self._resize_stambh_image()

    def _resize_stambh_image(self):
        image_path = Path(self.image.path)
        if not image_path.exists():
            return

        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGBA")
            alpha_box = image.getbbox()
            if alpha_box:
                image = image.crop(alpha_box)
            image = self._face_focused_portrait(image)
            if image_path.suffix.lower() == ".png":
                image.save(image_path, "PNG", optimize=True)
            else:
                background = Image.new("RGB", image.size, "#ead7c8")
                background.paste(image, mask=image.getchannel("A"))
                background.save(image_path, "JPEG", quality=90, optimize=True)

    def _face_focused_portrait(self, image):
        face_box = self._detect_face_box(image.convert("RGB"))
        width, height = image.size
        target_ratio = 4 / 5

        if face_box is not None:
            left, top, face_width, face_height = face_box
            center_x = left + face_width / 2
            center_y = top + face_height * 1.35
        else:
            center_x = width / 2
            center_y = height * 0.48

        crop_height = height
        crop_width = int(crop_height * target_ratio)
        if crop_width > width:
            crop_width = width
            crop_height = int(crop_width / target_ratio)

        left = max(0, min(width - crop_width, int(center_x - crop_width / 2)))
        top = max(0, min(height - crop_height, int(center_y - crop_height / 2)))
        image = image.crop((left, top, left + crop_width, top + crop_height))
        return image.resize((800, 1000), Image.Resampling.LANCZOS)

    def _detect_face_box(self, image):
        try:
            import cv2
            import numpy as np
        except ImportError:
            return None

        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        if len(faces) == 0:
            return None

        return max(faces, key=lambda face: face[2] * face[3])
