from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class SubscriptionPlan(models.Model):
    FREE = "free"
    PAID = "paid"

    PLAN_TYPES = (
        (FREE, "Free"),
        (PAID, "Paid"),
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.slug:
            # Django's Unicode slug validator strips Hindi combining marks
            # (matras/halant). Use a stable, valid generated slug instead of
            # saving a visually corrupted Hindi word.
            base_slug = slugify(self.name) or f"plan-{uuid4().hex[:8]}"
            candidate = base_slug
            suffix = 2
            while SubscriptionPlan.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base_slug}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

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


class PaymentTransaction(models.Model):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"

    STATUS_CHOICES = ((CREATED, "Created"), (PAID, "Paid"), (FAILED, "Failed"))

    subscription = models.OneToOneField(
        MembershipSubscription, on_delete=models.CASCADE, related_name="payment_transaction"
    )
    user_name = models.CharField(max_length=180)
    user_email = models.EmailField(blank=True)
    user_phone = models.CharField(max_length=30, blank=True)
    user_address = models.TextField(blank=True)
    plan_name = models.CharField(max_length=150)
    amount_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=CREATED)
    razorpay_order_id = models.CharField(max_length=120, unique=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    gateway_status = models.CharField(max_length=40, blank=True)
    failure_reason = models.TextField(blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.razorpay_order_id} - {self.get_status_display()}"


class InvoiceSequence(models.Model):
    financial_year = models.CharField(max_length=7, unique=True)
    next_number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.financial_year}: {self.next_number}"


class Invoice(models.Model):
    payment = models.OneToOneField(PaymentTransaction, on_delete=models.PROTECT, related_name="invoice")
    invoice_number = models.CharField(max_length=16, unique=True)
    issued_at = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, default="Annual membership fee")
    subtotal_paise = models.PositiveIntegerField()
    tax_paise = models.PositiveIntegerField(default=0)
    total_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-issued_at",)

    def __str__(self):
        return self.invoice_number

    @property
    def total_rupees(self):
        return self.total_paise / 100

    def get_absolute_url(self):
        return reverse("subscriptions:invoice", kwargs={"pk": self.pk})

    @classmethod
    def issue_for_payment(cls, payment):
        from django.db import transaction

        existing = cls.objects.filter(payment=payment).first()
        if existing:
            return existing
        today = timezone.localdate()
        start_year = today.year if today.month >= 4 else today.year - 1
        financial_year = f"{start_year}-{str(start_year + 1)[-2:]}"
        with transaction.atomic():
            sequence, _ = InvoiceSequence.objects.select_for_update().get_or_create(
                financial_year=financial_year
            )
            number = sequence.next_number
            sequence.next_number += 1
            sequence.save(update_fields=("next_number",))
            return cls.objects.create(
                payment=payment,
                invoice_number=f"DRS{str(start_year)[-2:]}-{number:06d}",
                description=f"{payment.plan_name} yearly membership donation",
                subtotal_paise=payment.amount_paise,
                tax_paise=0,
                total_paise=payment.amount_paise,
                currency=payment.currency,
            )


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
