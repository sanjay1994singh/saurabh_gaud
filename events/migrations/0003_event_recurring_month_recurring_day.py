from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0002_event_is_permanent_optional_start_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="recurring_day",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="For permanent yearly events, enter day of month.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="recurring_month",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "January"),
                    (2, "February"),
                    (3, "March"),
                    (4, "April"),
                    (5, "May"),
                    (6, "June"),
                    (7, "July"),
                    (8, "August"),
                    (9, "September"),
                    (10, "October"),
                    (11, "November"),
                    (12, "December"),
                ],
                help_text="For permanent yearly events, select the month.",
                null=True,
            ),
        ),
    ]
