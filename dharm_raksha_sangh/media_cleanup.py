from django.db.models.signals import post_delete, post_init, post_save


def register_file_cleanup(model, field_names):
    """
    Delete old uploaded files when file fields are replaced or model rows are removed.
    """

    field_names = tuple(field_names)
    original_attr = "_original_upload_names"
    uid_prefix = f"{model._meta.label_lower}.file_cleanup"

    def file_name(instance, field_name):
        file_obj = getattr(instance, field_name, None)
        return getattr(file_obj, "name", "") or ""

    def is_still_referenced(instance, field_name, name):
        if not name:
            return False
        queryset = model._default_manager.filter(**{field_name: name})
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        return queryset.exists()

    def delete_file(field, name):
        if name and field.storage.exists(name):
            field.storage.delete(name)

    def remember_original(sender, instance, **kwargs):
        setattr(
            instance,
            original_attr,
            {field_name: file_name(instance, field_name) for field_name in field_names},
        )

    def delete_changed_files(sender, instance, **kwargs):
        originals = getattr(instance, original_attr, {})
        for field_name in field_names:
            old_name = originals.get(field_name, "")
            new_name = file_name(instance, field_name)
            if old_name and old_name != new_name and not is_still_referenced(instance, field_name, old_name):
                field = instance._meta.get_field(field_name)
                delete_file(field, old_name)

        remember_original(sender, instance)

    def delete_current_files(sender, instance, **kwargs):
        for field_name in field_names:
            name = file_name(instance, field_name)
            if name and not is_still_referenced(instance, field_name, name):
                field = instance._meta.get_field(field_name)
                delete_file(field, name)

    post_init.connect(remember_original, sender=model, weak=False, dispatch_uid=f"{uid_prefix}.post_init")
    post_save.connect(delete_changed_files, sender=model, weak=False, dispatch_uid=f"{uid_prefix}.post_save")
    post_delete.connect(delete_current_files, sender=model, weak=False, dispatch_uid=f"{uid_prefix}.post_delete")
