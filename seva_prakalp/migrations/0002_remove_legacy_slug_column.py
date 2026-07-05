from django.db import migrations, models


def remove_legacy_slug_column(apps, schema_editor):
    SevaPrakalp = apps.get_model("seva_prakalp", "SevaPrakalp")
    table_name = SevaPrakalp._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    if "slug" not in existing_columns:
        return

    field = models.SlugField(max_length=220, unique=True, blank=True)
    field.set_attributes_from_name("slug")
    field.model = SevaPrakalp
    schema_editor.remove_field(SevaPrakalp, field)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("seva_prakalp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_slug_column, migrations.RunPython.noop),
    ]
