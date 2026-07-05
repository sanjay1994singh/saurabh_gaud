from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from PIL import Image, ImageOps


class Patrika(models.Model):
    title = models.CharField(max_length=220)
    issue_name = models.CharField(max_length=120, blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    pdf = models.FileField(
        upload_to="patrika/pdfs/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        help_text="Upload PDF patrika file.",
    )
    cover_image = models.ImageField(upload_to="patrika/covers/", blank=True, null=True)
    published_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "-published_date", "-created_at", "title")
        verbose_name = "patrika"
        verbose_name_plural = "patrika"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("patrika:detail", kwargs={"pk": self.pk})

    @property
    def file_name(self):
        return Path(self.pdf.name).name if self.pdf else ""

    @property
    def file_size_label(self):
        if not self.pdf:
            return ""
        try:
            size = self.pdf.size
        except OSError:
            return ""
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        return f"{size / 1024:.0f} KB"

    @property
    def date_label(self):
        if self.published_date:
            return self.published_date.strftime("%d %b %Y")
        return "Latest issue"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cover_image:
            self._resize_cover_image()

    def _resize_cover_image(self):
        image_path = Path(self.cover_image.path)
        if not image_path.exists():
            return

        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image = ImageOps.fit(image, (900, 1200), method=Image.Resampling.LANCZOS)
            image_format = "PNG" if image_path.suffix.lower() == ".png" else "JPEG"
            save_kwargs = {"optimize": True}
            if image_format == "JPEG":
                save_kwargs["quality"] = 90
            image.save(image_path, image_format, **save_kwargs)

