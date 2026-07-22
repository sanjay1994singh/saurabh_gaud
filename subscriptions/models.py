from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class SubscriptionPlan(models.Model):
    FREE = "free"
    PAID = "paid"

    PLAN_TYPES = (
        (FREE, "Free"),
        (PAID, "Paid"),
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    plan_type = models.CharField(max_length=12, choices=PLAN_TYPES, default=FREE)
    member_type_text = models.CharField(
        max_length=150,
        blank=True,
        help_text="Text printed as member type on certificate. Leave blank to use plan name.",
    )
    description = models.TextField(blank=True)
    amount = models.PositiveIntegerField(default=0, help_text="Amount in INR.")
    duration_days = models.PositiveIntegerField(default=365)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "amount", "name")

    def __str__(self):
        return self.name

    @property
    def amount_paise(self):
        return self.amount * 100

    @property
    def is_free(self):
        return self.plan_type == self.FREE or self.amount == 0

    @property
    def plan_type_label(self):
        return "निशुल्क" if self.is_free else "पेड / Paid"

    @property
    def certificate_member_type(self):
        return self.member_type_text or self.name

    def get_absolute_url(self):
        return reverse("subscriptions:join", kwargs={"slug": self.slug})


class MembershipSubscription(models.Model):
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    EXPIRED = "expired"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (FAILED, "Failed"),
        (EXPIRED, "Expired"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=120, blank=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} - {self.plan}"

    @property
    def is_active(self):
        return self.status == self.ACTIVE and (self.ends_at is None or self.ends_at >= timezone.now())

    @property
    def status_label(self):
        labels = {
            self.PENDING: "लंबित",
            self.ACTIVE: "सक्रिय",
            self.FAILED: "असफल",
            self.EXPIRED: "समाप्त",
        }
        return labels.get(self.status, self.get_status_display())

    def activate(self):
        now = timezone.now()
        self.status = self.ACTIVE
        self.starts_at = now
        self.ends_at = now + timedelta(days=self.plan.duration_days)
        self.save(update_fields=("status", "starts_at", "ends_at", "updated_at"))
        Certificate.objects.get_or_create(user=self.user, subscription=self)


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    subscription = models.OneToOneField(
        MembershipSubscription,
        on_delete=models.CASCADE,
        related_name="certificate",
    )
    certificate_number = models.CharField(max_length=32, unique=True, blank=True)
    issued_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-issued_at",)

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = f"DRS-{timezone.now():%Y%m}-{uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.certificate_number

    def get_absolute_url(self):
        return reverse("subscriptions:certificate", kwargs={"pk": self.pk})
