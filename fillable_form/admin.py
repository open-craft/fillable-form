from django.contrib import admin
from .models import FillableFormField, FormResponse


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = (
        "user", "course_key", "usage_key", "form_group_id",
        "modified", "created",
    )
    list_filter = ("course_key", "form_group_id")
    search_fields = ("user__username", "user__email", "form_group_id")
    raw_id_fields = ("user",)
    readonly_fields = ("created", "modified")


@admin.register(FillableFormField)
class FillableFormFieldAdmin(admin.ModelAdmin):
    list_display = (
        "course_key", "usage_key", "form_group_id",
        "field_label", "pdf_order", "modified",
    )
    list_filter = ("course_key", "form_group_id")
    search_fields = ("course_key", "usage_key", "form_group_id", "field_label")
    readonly_fields = ("created", "modified")
