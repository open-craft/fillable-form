# Add FillableFormField registry model for author-managed PDF ordering

from django.db import migrations, models
import opaque_keys.edx.django.models


class Migration(migrations.Migration):
    dependencies = [
        ("fillable_form", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FillableFormField",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, db_index=True),
                ),
                (
                    "course_key",
                    opaque_keys.edx.django.models.CourseKeyField(
                        db_index=True, max_length=255
                    ),
                ),
                (
                    "usage_key",
                    opaque_keys.edx.django.models.UsageKeyField(
                        max_length=255, unique=True
                    ),
                ),
                (
                    "form_group_id",
                    models.CharField(db_index=True, max_length=255),
                ),
                (
                    "field_label",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "instructions",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "pdf_order",
                    models.IntegerField(db_index=True, default=0),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["course_key", "form_group_id", "pdf_order"],
                        name="ff_course_group_pdforder_idx",
                    ),
                ],
            },
        ),
    ]
