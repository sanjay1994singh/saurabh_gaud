# Generated manually for image-based patrika reader pages.

from django.db import migrations, models
import django.db.models.deletion
import patrika.models


class Migration(migrations.Migration):

    dependencies = [
        ("patrika", "0002_use_safe_upload_names"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatrikaPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField()),
                ("image", models.FileField(upload_to=patrika.models.patrika_page_upload_to)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "patrika",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pages",
                        to="patrika.patrika",
                    ),
                ),
            ],
            options={
                "ordering": ("number",),
                "unique_together": {("patrika", "number")},
            },
        ),
    ]
