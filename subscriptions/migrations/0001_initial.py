from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("slug", models.SlugField(unique=True)),
                (
                    "plan_type",
                    models.CharField(
                        choices=[("free", "Free"), ("paid", "Paid")],
                        default="free",
                        max_length=12,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("amount", models.PositiveIntegerField(default=0, help_text="Amount in INR.")),
                ("duration_days", models.PositiveIntegerField(default=365)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("display_order", "amount", "name"),
            },
        ),
        migrations.CreateModel(
            name="MembershipSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("active", "Active"),
                            ("failed", "Failed"),
                            ("expired", "Expired"),
                        ],
                        default="pending",
                        max_length=12,
                    ),
                ),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("razorpay_order_id", models.CharField(blank=True, max_length=120)),
                ("razorpay_payment_id", models.CharField(blank=True, max_length=120)),
                ("razorpay_signature", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="memberships",
                        to="subscriptions.subscriptionplan",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Certificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("certificate_number", models.CharField(blank=True, max_length=32, unique=True)),
                ("issued_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "subscription",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="certificate",
                        to="subscriptions.membershipsubscription",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="certificates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-issued_at",),
            },
        ),
    ]
