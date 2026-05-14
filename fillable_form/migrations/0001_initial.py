# Generated migration for the initial FormResponse model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opaque_keys.edx.django.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FormResponse",
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
                        db_index=True, max_length=255
                    ),
                ),
                (
                    "form_group_id",
                    models.CharField(db_index=True, max_length=255),
                ),
                ("response_text", models.TextField(blank=True, default="")),
                (
                    "user",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-modified"],
                "indexes": [
                    models.Index(
                        fields=["course_key", "form_group_id"],
                        name="ff_course_formgroup_idx",
                    ),
                    models.Index(
                        fields=["user", "course_key", "form_group_id"],
                        name="ff_user_course_formgroup_idx",
                    ),
                ],
                "unique_together": {("user", "usage_key")},
            },
        ),
    ]
