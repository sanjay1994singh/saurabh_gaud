# Generated manually for the patrika app.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Patrika",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220)),
                ("issue_name", models.CharField(blank=True, max_length=120)),
                ("short_description", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "pdf",
                    models.FileField(
                        help_text="Upload PDF patrika file.",
                        upload_to="patrika/pdfs/",
                        validators=[django.core.validators.FileExtensionValidator(allowed_extensions=["pdf"])],
                    ),
                ),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="patrika/covers/")),
                ("published_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "patrika",
                "verbose_name_plural": "patrika",
                "ordering": ("display_order", "-published_date", "-created_at", "title"),
            },
        ),
    ]
