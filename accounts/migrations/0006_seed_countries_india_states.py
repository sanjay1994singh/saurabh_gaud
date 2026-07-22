from django.db import migrations

from accounts.location_data import COUNTRIES, INDIA_STATES


def seed_locations(apps, schema_editor):
    Country = apps.get_model("accounts", "Country")
    State = apps.get_model("accounts", "State")

    country_by_code = {}
    for code, name in COUNTRIES:
        country, _ = Country.objects.update_or_create(
            code=code,
            defaults={"name": name, "is_active": True},
        )
        country_by_code[code] = country

    india = country_by_code.get("IN")
    if india:
        for state_name in INDIA_STATES:
            State.objects.update_or_create(
                country=india,
                name=state_name,
                defaults={"is_active": True},
            )


def unseed_locations(apps, schema_editor):
    Country = apps.get_model("accounts", "Country")
    State = apps.get_model("accounts", "State")
    india = Country.objects.filter(code="IN").first()
    if india:
        State.objects.filter(country=india, name__in=INDIA_STATES).delete()
    Country.objects.filter(code__in=[code for code, _name in COUNTRIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_country_user_country_state_user_state_obj"),
    ]

    operations = [
        migrations.RunPython(seed_locations, unseed_locations),
    ]
