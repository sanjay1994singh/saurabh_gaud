from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("subscriptions", "0004_paymenttransaction_subscriptionplan_slug")]

    operations = [
        migrations.CreateModel(
            name="InvoiceSequence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("financial_year", models.CharField(max_length=7, unique=True)),
                ("next_number", models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_number", models.CharField(max_length=16, unique=True)),
                ("issued_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("description", models.CharField(default="Annual membership fee", max_length=255)),
                ("subtotal_paise", models.PositiveIntegerField()),
                ("tax_paise", models.PositiveIntegerField(default=0)),
                ("total_paise", models.PositiveIntegerField()),
                ("currency", models.CharField(default="INR", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("payment", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="invoice", to="subscriptions.paymenttransaction")),
            ],
            options={"ordering": ("-issued_at",)},
        ),
    ]
