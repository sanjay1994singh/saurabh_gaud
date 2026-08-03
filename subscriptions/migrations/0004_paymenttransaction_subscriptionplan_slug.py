from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("subscriptions", "0003_subscriptionplan_member_type_text")]

    operations = [
        migrations.AlterField(
            model_name="subscriptionplan",
            name="slug",
            field=models.SlugField(blank=True, max_length=180, unique=True),
        ),
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_name", models.CharField(max_length=180)),
                ("user_email", models.EmailField(blank=True, max_length=254)),
                ("user_phone", models.CharField(blank=True, max_length=30)),
                ("user_address", models.TextField(blank=True)),
                ("plan_name", models.CharField(max_length=150)),
                ("amount_paise", models.PositiveIntegerField()),
                ("currency", models.CharField(default="INR", max_length=3)),
                ("status", models.CharField(choices=[("created", "Created"), ("paid", "Paid"), ("failed", "Failed")], default="created", max_length=12)),
                ("razorpay_order_id", models.CharField(max_length=120, unique=True)),
                ("razorpay_payment_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("razorpay_signature", models.CharField(blank=True, max_length=255)),
                ("gateway_status", models.CharField(blank=True, max_length=40)),
                ("failure_reason", models.TextField(blank=True)),
                ("gateway_response", models.JSONField(blank=True, default=dict)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("subscription", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment_transaction", to="subscriptions.membershipsubscription")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
