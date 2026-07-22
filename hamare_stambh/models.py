from django.db import models
from django.urls import reverse

from dharm_raksha_sangh.image_utils import face_focused_portrait, optimize_image_file


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
        optimize_image_file(
            self.image.path,
            fit_size=(800, 1000),
            quality=82,
            background="#ead7c8",
            crop_alpha=True,
            pre_crop=face_focused_portrait,
        )
