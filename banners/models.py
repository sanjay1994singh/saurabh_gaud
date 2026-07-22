from django.db import models
from django.utils import timezone

from dharm_raksha_sangh.image_utils import optimize_image_file


class Banner(models.Model):
    HEADER_TOP = "header_top"
    HOME_AFTER_HERO = "home_after_hero"
    HOME_MIDDLE = "home_middle"
    FOOTER_TOP = "footer_top"
    SIDEBAR = "sidebar"

    PLACEMENT_CHOICES = (
        (HEADER_TOP, "Header top - below main navigation on every page"),
        (HOME_AFTER_HERO, "Home after hero - below homepage hero"),
        (HOME_MIDDLE, "Home middle - above Hamare Stambh section"),
        (FOOTER_TOP, "Footer top - above footer on every page"),
        (SIDEBAR, "Sidebar - reusable for detail pages later"),
    )

    title = models.CharField(max_length=160)
    placement = models.CharField(max_length=40, choices=PLACEMENT_CHOICES)
    image = models.ImageField(upload_to="banners/", blank=True, null=True)
    text = models.CharField(max_length=255, blank=True)
    link_url = models.URLField(blank=True)
    link_label = models.CharField(max_length=80, blank=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    show_everywhere = models.BooleanField(
        default=False,
        help_text="Show this banner in every available banner/ad slot instead of only the selected placement.",
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "display_order")

    def __str__(self):
        return f"{self.title} ({self.get_placement_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            optimize_image_file(self.image.path, max_size=(1800, 600), quality=82, background="#ffffff")

    @property
    def is_live(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at < now:
            return False
        return True
