from pathlib import Path
from uuid import uuid4

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

from dharm_raksha_sangh.image_utils import optimize_image_file


def patrika_pdf_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower() or ".pdf"
    return f"patrika/pdfs/{uuid4().hex}{suffix}"


def patrika_cover_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower() or ".jpg"
    return f"patrika/covers/{uuid4().hex}{suffix}"


def patrika_page_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower() or ".png"
    return f"patrika/pages/{uuid4().hex}{suffix}"


class Patrika(models.Model):
    title = models.CharField(max_length=220)
    issue_name = models.CharField(max_length=120, blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    pdf = models.FileField(
        upload_to=patrika_pdf_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        help_text="Upload PDF patrika file.",
    )
    cover_image = models.ImageField(upload_to=patrika_cover_upload_to, blank=True, null=True)
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

    @property
    def page_count(self):
        return self.pages.count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cover_image:
            self._resize_cover_image()

    def _resize_cover_image(self):
        optimize_image_file(self.cover_image.path, fit_size=(900, 1200), quality=82, background="#ffffff")


class PatrikaPage(models.Model):
    patrika = models.ForeignKey(Patrika, related_name="pages", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    image = models.FileField(upload_to=patrika_page_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("number",)
        unique_together = ("patrika", "number")

    def __str__(self):
        return f"{self.patrika} page {self.number:02d}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            optimize_image_file(self.image.path, max_size=(1800, 2400), quality=82, background="#ffffff")
