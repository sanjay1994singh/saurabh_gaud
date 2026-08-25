from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_user_district_user_pin_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="father_spouse_name",
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
