# Generated manually to keep patrika uploads safe for Unicode filenames.

import django.core.validators
from django.db import migrations, models
import patrika.models


class Migration(migrations.Migration):

    dependencies = [
        ("patrika", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patrika",
            name="cover_image",
            field=models.ImageField(blank=True, null=True, upload_to=patrika.models.patrika_cover_upload_to),
        ),
        migrations.AlterField(
            model_name="patrika",
            name="pdf",
            field=models.FileField(
                help_text="Upload PDF patrika file.",
                upload_to=patrika.models.patrika_pdf_upload_to,
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=["pdf"])],
            ),
        ),
    ]
