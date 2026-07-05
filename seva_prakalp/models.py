from pathlib import Path

from django.db import models
from django.urls import reverse
from PIL import Image, ImageOps


class SevaPrakalp(models.Model):
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to="seva_prakalp/", blank=True, null=True)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")
        verbose_name = "seva prakalp"
        verbose_name_plural = "seva prakalp"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("seva_prakalp:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            self._resize_prakalp_image()

    def _resize_prakalp_image(self):
        image_path = Path(self.image.path)
        if not image_path.exists():
            return

        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image = ImageOps.fit(image, (1200, 760), method=Image.Resampling.LANCZOS)
            image_format = "PNG" if image_path.suffix.lower() == ".png" else "JPEG"
            save_kwargs = {"optimize": True}
            if image_format == "JPEG":
                save_kwargs["quality"] = 90
            image.save(image_path, image_format, **save_kwargs)
