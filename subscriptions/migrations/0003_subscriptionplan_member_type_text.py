from django.db import migrations, models


def fill_default_member_types(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    for plan in SubscriptionPlan.objects.filter(member_type_text=""):
        plan.member_type_text = plan.name
        plan.save(update_fields=("member_type_text",))


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0002_default_subscription_plans"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriptionplan",
            name="member_type_text",
            field=models.CharField(
                blank=True,
                help_text="Text printed as member type on certificate. Leave blank to use plan name.",
                max_length=150,
            ),
        ),
        migrations.RunPython(fill_default_member_types, migrations.RunPython.noop),
    ]
