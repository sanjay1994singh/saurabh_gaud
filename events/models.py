from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from PIL import Image, ImageOps


class Event(models.Model):
    MONTH_CHOICES = (
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    )

    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    venue = models.CharField(max_length=180, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    recurring_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        blank=True,
        null=True,
        help_text="For permanent yearly events, select the month.",
    )
    recurring_day = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="For permanent yearly events, enter day of month.",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_permanent = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "-start_date", "title")

    def __str__(self):
        return self.title

    @property
    def is_past(self):
        if self.is_permanent or not self.start_date:
            return False
        event_end = self.end_date or self.start_date
        return event_end < timezone.localdate()

    @property
    def status_label(self):
        if self.is_permanent:
            return "Permanent Event"
        return "Past Event" if self.is_past else "Present Event"

    @property
    def date_label(self):
        if self.is_permanent and self.recurring_month and self.recurring_day:
            return f"Every {self.get_recurring_month_display()} {self.recurring_day}"
        if self.start_date:
            return self.start_date.strftime("%d %b %Y")
        return "Any time"

    def clean(self):
        super().clean()
        if self.recurring_day is not None and not 1 <= self.recurring_day <= 31:
            raise ValidationError({"recurring_day": "Day must be between 1 and 31."})
        if bool(self.recurring_month) != bool(self.recurring_day):
            raise ValidationError("Select both recurring month and recurring day, or leave both blank.")

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            self._resize_event_image()

    def _resize_event_image(self):
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
