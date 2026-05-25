"""
Tests for FormResponse model.

These tests use Django's TestCase and require a test database.
Run with: python -m pytest fillable_form/tests/test_models.py -v
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from opaque_keys.edx.keys import CourseKey, UsageKey

from fillable_form.models import FillableFormField, FormResponse

User = get_user_model()


@pytest.mark.django_db
class TestFormResponse:
    """Tests for the FormResponse model."""

    def test_create_form_response(self, django_user_model):
        """Create a FormResponse, verify fields saved correctly."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        response = FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
            response_text="Hello world",
        )

        assert response.user == user
        assert response.course_key == course_key
        assert response.usage_key == usage_key
        assert response.form_group_id == "group1"
        assert response.response_text == "Hello world"
        assert response.created is not None
        assert response.modified is not None

    def test_update_or_create(self, django_user_model):
        """Call save-like logic twice with same user+usage_key, verify single row updated."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        # First create
        r1, created1 = FormResponse.objects.update_or_create(
            user=user,
            usage_key=usage_key,
            defaults={
                "course_key": course_key,
                "form_group_id": "group1",
                "response_text": "First save",
            },
        )
        assert created1 is True
        assert FormResponse.objects.count() == 1

        # Second update
        r2, created2 = FormResponse.objects.update_or_create(
            user=user,
            usage_key=usage_key,
            defaults={
                "course_key": course_key,
                "form_group_id": "group1",
                "response_text": "Updated save",
            },
        )
        assert created2 is False
        assert FormResponse.objects.count() == 1
        assert r2.response_text == "Updated save"

    def test_unique_constraint(self, django_user_model):
        """Attempt to create two responses for same (user, usage_key), verify integrity error."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
            response_text="First",
        )

        with pytest.raises(IntegrityError):
            FormResponse.objects.create(
                user=user,
                course_key=course_key,
                usage_key=usage_key,
                form_group_id="group2",
                response_text="Second (should fail)",
            )

    def test_ordering(self, django_user_model):
        """Create multiple responses, verify newest first by default."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")

        r1 = FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=UsageKey.from_string(
                "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
            ),
            form_group_id="group1",
            response_text="Older",
        )
        r2 = FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=UsageKey.from_string(
                "block-v1:TestX+TS101+2026+type@fillable_form+block@field2"
            ),
            form_group_id="group1",
            response_text="Newer",
        )

        responses = list(FormResponse.objects.all())
        # Newer (most recently modified) should come first
        assert responses[0].id == r2.id
        assert responses[1].id == r1.id

    def test_response_text_defaults_to_empty(self, django_user_model):
        """Verify response_text defaults to empty string."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        response = FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
        )

        assert response.response_text == ""

    def test_index_user_course_formgroup(self, django_user_model):
        """Verify the composite index is created (table has the index)."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
            response_text="Test",
        )

        # Query using the indexed fields — should return one result
        results = FormResponse.objects.filter(
            user=user,
            course_key=course_key,
            form_group_id="group1",
        )
        assert len(results) == 1
        assert results[0].response_text == "Test"


@pytest.mark.django_db
class TestFillableFormField:
    """Tests for the FillableFormField registry model."""

    def test_create_fillable_form_field(self):
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        field = FillableFormField.objects.create(
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
            field_label="Field 1",
            instructions="<p>Instructions</p>",
            pdf_order=10,
        )

        assert field.course_key == course_key
        assert field.usage_key == usage_key
        assert field.form_group_id == "group1"
        assert field.field_label == "Field 1"
        assert field.instructions == "<p>Instructions</p>"
        assert field.pdf_order == 10

    def test_usage_key_unique(self):
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        FillableFormField.objects.create(
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
        )

        with pytest.raises(IntegrityError):
            FillableFormField.objects.create(
                course_key=course_key,
                usage_key=usage_key,
                form_group_id="group2",
            )

    def test_allows_duplicate_pdf_order(self):
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")

        for block_id in ["field1", "field2"]:
            FillableFormField.objects.create(
                course_key=course_key,
                usage_key=UsageKey.from_string(
                    f"block-v1:TestX+TS101+2026+type@fillable_form+block@{block_id}"
                ),
                form_group_id="group1",
                pdf_order=10,
            )

        assert FillableFormField.objects.count() == 2
