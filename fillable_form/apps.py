from django.apps import AppConfig
from django.utils.translation import gettext as _


class FillableFormConfig(AppConfig):
    name = "fillable_form"
    verbose_name = _("Fillable Form")
    default_auto_field = "django.db.models.BigAutoField"

    plugin_app = {}
