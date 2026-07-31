from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField


class FormResponse(TimeStampedModel):
    """Stores a student's response to a single fillable form field."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
    )
    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = UsageKeyField(max_length=255, db_index=True)
    form_group_id = models.CharField(max_length=255, db_index=True)
    response_text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "fillable_form"
        unique_together = ("user", "usage_key")
        ordering = ["-modified"]
        indexes = [
            models.Index(fields=["course_key", "form_group_id"], name="ff_course_formgroup_idx"),
            models.Index(fields=["user", "course_key", "form_group_id"], name="ff_user_course_formgroup_idx"),
        ]


class FillableFormField(TimeStampedModel):
    """Stores author metadata for one fillable form XBlock field."""

    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = UsageKeyField(max_length=255, unique=True)
    form_group_id = models.CharField(max_length=255, db_index=True)
    field_label = models.CharField(max_length=255, blank=True, default="")
    instructions = models.TextField(blank=True, default="")
    pdf_order = models.IntegerField(default=0, db_index=True)

    class Meta:
        app_label = "fillable_form"
        indexes = [
            models.Index(fields=["course_key", "form_group_id", "pdf_order"], name="ff_course_group_pdforder_idx"),
        ]
