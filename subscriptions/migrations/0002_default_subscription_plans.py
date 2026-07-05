from django.db import migrations


def create_default_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.get_or_create(
        slug="free-member",
        defaults={
            "name": "Free Member",
            "plan_type": "free",
            "description": "Basic membership with downloadable certificate.",
            "amount": 0,
            "duration_days": 365,
            "display_order": 1,
        },
    )
    SubscriptionPlan.objects.get_or_create(
        slug="annual-member",
        defaults={
            "name": "Annual Member",
            "plan_type": "paid",
            "description": "Paid annual membership with verified payment and certificate.",
            "amount": 501,
            "duration_days": 365,
            "display_order": 2,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_plans, migrations.RunPython.noop),
    ]
