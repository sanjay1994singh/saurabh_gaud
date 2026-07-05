from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("banners", "0002_demo_banners"),
    ]

    operations = [
        migrations.AddField(
            model_name="banner",
            name="show_everywhere",
            field=models.BooleanField(
                default=False,
                help_text="Show this banner in every available banner/ad slot instead of only the selected placement.",
            ),
        ),
    ]
