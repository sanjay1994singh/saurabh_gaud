# Generated for the initial Seva Prakalp app scaffold.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SevaPrakalp",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                (
                    "short_description",
                    models.CharField(blank=True, max_length=255),
                ),
                ("content", models.TextField()),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="seva_prakalp/",
                    ),
                ),
                ("location", models.CharField(blank=True, max_length=150)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "seva prakalp",
                "verbose_name_plural": "seva prakalp",
                "ordering": ("display_order", "name"),
            },
        ),
    ]
