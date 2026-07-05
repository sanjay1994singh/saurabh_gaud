from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_member_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="members/photos/"),
        ),
    ]
