from django.apps import AppConfig


class FillableFormConfig(AppConfig):
    name = "fillable_form"
    verbose_name = "Fillable Form"
    default_auto_field = "django.db.models.BigAutoField"

    plugin_app = {}
