from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Banner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                (
                    "placement",
                    models.CharField(
                        choices=[
                            ("header_top", "Header top - below main navigation on every page"),
                            ("home_after_hero", "Home after hero - below homepage hero"),
                            ("home_middle", "Home middle - above Hamare Stambh section"),
                            ("footer_top", "Footer top - above footer on every page"),
                            ("sidebar", "Sidebar - reusable for detail pages later"),
                        ],
                        max_length=40,
                    ),
                ),
                ("image", models.ImageField(blank=True, null=True, upload_to="banners/")),
                ("text", models.CharField(blank=True, max_length=255)),
                ("link_url", models.URLField(blank=True)),
                ("link_label", models.CharField(blank=True, max_length=80)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("placement", "display_order", "-created_at"),
            },
        ),
    ]
