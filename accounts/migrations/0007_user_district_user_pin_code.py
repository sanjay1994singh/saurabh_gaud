from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_seed_countries_india_states"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="district",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="user",
            name="pin_code",
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
