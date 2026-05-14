"""
Tests for the service layer.

Run with: python -m pytest fillable_form/tests/test_services.py -v
"""
import pytest
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey, UsageKey

from fillable_form.models import FillableFormField, FormResponse
from fillable_form.services import (
    get_form_group_options,
    get_form_group_responses,
    get_registered_form_fields,
    get_response,
    save_response,
    save_form_field,
)

User = get_user_model()


@pytest.mark.django_db
class TestSaveAndGetResponse:
    """Tests for save_response and get_response."""

    def test_save_response_new(self, django_user_model):
        """save_response() creates a new row when none exists."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        response = save_response(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
            response_text="Hello world",
        )

        assert FormResponse.objects.count() == 1
        assert response.response_text == "Hello world"
        assert response.form_group_id == "group1"

    def test_save_response_update(self, django_user_model):
        """save_response() updates existing row when one exists."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        # Initial save
        save_response(user, course_key, usage_key, "group1", "First draft")

        # Update
        response = save_response(user, course_key, usage_key, "group1", "Final answer")

        assert FormResponse.objects.count() == 1
        assert response.response_text == "Final answer"

    def test_get_response_exists(self, django_user_model):
        """get_response() returns text when row exists."""
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
            response_text="My response",
        )

        result = get_response(user, usage_key)
        assert result == "My response"

    def test_get_response_missing(self, django_user_model):
        """get_response() returns '' when no row exists."""
        user = django_user_model.objects.create(username="testuser")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@nonexistent"
        )

        result = get_response(user, usage_key)
        assert result == ""


@pytest.mark.django_db
class TestGetFormGroupResponses:
    """Tests for get_form_group_responses."""

    def test_get_form_group_responses(self, django_user_model):
        """Returns dict mapping usage_key -> response_text."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")

        uk1 = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )
        uk2 = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field2"
        )

        FormResponse.objects.create(
            user=user, course_key=course_key, usage_key=uk1,
            form_group_id="app", response_text="Answer 1",
        )
        FormResponse.objects.create(
            user=user, course_key=course_key, usage_key=uk2,
            form_group_id="app", response_text="Answer 2",
        )

        result = get_form_group_responses(user, course_key, [uk1, uk2])
        assert len(result) == 2
        assert result[str(uk1)] == "Answer 1"
        assert result[str(uk2)] == "Answer 2"

    def test_get_form_group_responses_empty(self, django_user_model):
        """Returns empty dict when no responses exist."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")

        result = get_form_group_responses(user, course_key, [])
        assert result == {}

    def test_scoped_to_course_and_user(self, django_user_model):
        """Responses from other users/courses are not returned."""
        user1 = django_user_model.objects.create(username="user1")
        user2 = django_user_model.objects.create(username="user2")
        course_a = CourseKey.from_string("course-v1:A+TS101+2026")
        course_b = CourseKey.from_string("course-v1:B+TS101+2026")
        uk = UsageKey.from_string(
            "block-v1:A+TS101+2026+type@fillable_form+block@field1"
        )

        FormResponse.objects.create(
            user=user1, course_key=course_a, usage_key=uk,
            form_group_id="g1", response_text="User1's answer",
        )
        FormResponse.objects.create(
            user=user2, course_key=course_a, usage_key=uk,
            form_group_id="g1", response_text="User2's answer",
        )

        result = get_form_group_responses(user1, course_a, [uk])
        assert len(result) == 1
        assert list(result.values())[0] == "User1's answer"

    def test_finds_response_when_saved_group_is_stale(self, django_user_model):
        """PDF lookup follows registered usage keys, not stale response group IDs."""
        user = django_user_model.objects.create(username="testuser")
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )
        FormResponse.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="old-group",
            response_text="Existing answer",
        )

        result = get_form_group_responses(user, course_key, [usage_key])

        assert result[str(usage_key)] == "Existing answer"


class TestGetFormGroupOptions:
    """Tests for get_form_group_options."""

    @pytest.mark.django_db
    def test_returns_sorted_distinct_ids(self, django_user_model):
        """Returns sorted distinct form group IDs from FillableFormField registry."""
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")

        for group_id, block_id in [("beta", "b1"), ("alpha", "b2"), ("beta", "b3"), ("gamma", "b4")]:
            FillableFormField.objects.create(
                course_key=course_key,
                usage_key=UsageKey.from_string(
                    f"block-v1:TestX+TS101+2026+type@fillable_form+block@{block_id}"
                ),
                form_group_id=group_id,
                field_label=group_id,
                pdf_order=0,
            )

        result = get_form_group_options(course_key)
        assert result == ["alpha", "beta", "gamma"]

    @pytest.mark.django_db
    def test_returns_empty_list(self):
        """Returns empty list when no registry rows exist for the course."""
        course_key = CourseKey.from_string("course-v1:EmptyX+TS101+2026")
        result = get_form_group_options(course_key)
        assert result == []

    @pytest.mark.django_db
    def test_excludes_empty_string(self):
        """Rows with form_group_id='' are not included."""
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        FillableFormField.objects.create(
            course_key=course_key,
            usage_key=UsageKey.from_string(
                "block-v1:TestX+TS101+2026+type@fillable_form+block@empty1"
            ),
            form_group_id="",
            field_label="empty",
            pdf_order=0,
        )
        FillableFormField.objects.create(
            course_key=course_key,
            usage_key=UsageKey.from_string(
                "block-v1:TestX+TS101+2026+type@fillable_form+block@alpha1"
            ),
            form_group_id="alpha",
            field_label="alpha",
            pdf_order=0,
        )

        result = get_form_group_options(course_key)
        assert "" not in result
        assert result == ["alpha"]


@pytest.mark.django_db
class TestFormFieldRegistry:
    """Tests for registered form field metadata."""

    def test_save_form_field_creates_row(self):
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )

        row = save_form_field(
            course_key=course_key,
            usage_key=usage_key,
            form_group_id="group1",
            field_label="Field 1",
            instructions="<p>Instructions</p>",
            pdf_order=10,
        )

        assert row.form_group_id == "group1"
        assert row.field_label == "Field 1"
        assert row.pdf_order == 10

    def test_save_form_field_updates_existing_row(self):
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        usage_key = UsageKey.from_string(
            "block-v1:TestX+TS101+2026+type@fillable_form+block@field1"
        )
        save_form_field(course_key, usage_key, "old", "Old", "", 10)

        row = save_form_field(course_key, usage_key, "new", "New", "Text", 20)

        assert FillableFormField.objects.count() == 1
        assert row.form_group_id == "new"
        assert row.field_label == "New"
        assert row.instructions == "Text"
        assert row.pdf_order == 20

    def test_get_registered_form_fields_orders_deterministically(self):
        course_key = CourseKey.from_string("course-v1:TestX+TS101+2026")
        fields = [
            ("b", "Beta", 10),
            ("a", "Alpha", 10),
            ("c", "Gamma", 5),
        ]
        for block_id, label, order in fields:
            FillableFormField.objects.create(
                course_key=course_key,
                usage_key=UsageKey.from_string(
                    f"block-v1:TestX+TS101+2026+type@fillable_form+block@{block_id}"
                ),
                form_group_id="group1",
                field_label=label,
                pdf_order=order,
            )

        result = list(get_registered_form_fields(course_key, "group1"))

        assert [field.field_label for field in result] == ["Gamma", "Alpha", "Beta"]
