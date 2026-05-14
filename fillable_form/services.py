from typing import Any

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from .models import FillableFormField, FormResponse

User = get_user_model()


def get_response(user: User, usage_key: Any) -> str:
    """
    Get a student's response for a specific XBlock instance.

    Args:
        user: Django User instance
        usage_key: UsageKey for the XBlock

    Returns:
        str: The response text, or "" if no response exists.
    """
    try:
        return FormResponse.objects.get(
            user=user, usage_key=usage_key
        ).response_text
    except FormResponse.DoesNotExist:
        return ""


def save_response(user: User, course_key: Any, usage_key: Any, form_group_id: str, response_text: str) -> FormResponse:
    """
    Save or update a student's response to a field.

    Uses update_or_create so repeated saves on the same field
    update the existing row rather than creating duplicates.

    Args:
        user: Django User
        course_key: CourseKey
        usage_key: UsageKey of the XBlock being filled
        form_group_id: str — the author-configured form group identifier
        response_text: str — the student's text

    Returns:
        FormResponse
    """
    response, _ = FormResponse.objects.update_or_create(
        user=user,
        usage_key=usage_key,
        defaults={
            "course_key": course_key,
            "form_group_id": form_group_id,
            "response_text": response_text,
        },
    )
    return response


def get_form_group_responses(user: User, course_key: Any, usage_keys: list[Any]) -> dict[str, str]:
    """
    Get a student's responses for the registered fields in a form group.

    Returns a dict mapping usage_key (str) -> response_text.

    Args:
        user: Django User
        course_key: CourseKey
        usage_keys: UsageKeys for the registered fields in the form group

    Returns:
        dict[str, str]
    """
    if not usage_keys:
        return {}

    responses = (
        FormResponse.objects
        .filter(user=user, course_key=course_key, usage_key__in=usage_keys)
        .order_by()
        .values_list("usage_key", "response_text")
    )
    return {str(usage_key): response_text for usage_key, response_text in responses}


def get_form_group_options(course_key: Any) -> list[str]:
    """
    Get all distinct form group IDs registered in a course.

    Queries the FillableFormField registry (populated on every Studio
    save) so we avoid walking the full course block structure.

    Used by the Studio view to populate the Creatable dropdown so
    authors can pick an existing group or type a new one.

    Args:
        course_key: CourseKey

    Returns:
        list[str]: Sorted distinct form group IDs (excluding empty string).
    """
    return sorted(
        FillableFormField.objects
        .filter(course_key=course_key)
        .exclude(form_group_id="")
        .order_by("form_group_id")
        .values_list("form_group_id", flat=True)
        .distinct()
    )


def save_form_field(
    course_key: Any,
    usage_key: Any,
    form_group_id: str,
    field_label: str,
    instructions: str,
    pdf_order: int,
) -> FillableFormField:
    """Persist author metadata into the FillableFormField registry.

    Called from ``studio_submit`` after XBlock settings are saved so the
    registry stays in sync with the authoring source of truth.
    """
    row, _ = FillableFormField.objects.update_or_create(
        usage_key=usage_key,
        defaults={
            "course_key": course_key,
            "form_group_id": form_group_id,
            "field_label": field_label,
            "instructions": instructions,
            "pdf_order": pdf_order,
        },
    )
    return row


def get_registered_form_fields(
    course_key: Any,
    form_group_id: str,
) -> QuerySet[FillableFormField]:
    """Return all registered fields for a form group in PDF order.

    Ordering by ``pdf_order``, then ``field_label``, then ``usage_key``
    keeps duplicate ``pdf_order`` values deterministic.
    """
    return (
        FillableFormField.objects
        .filter(course_key=course_key, form_group_id=form_group_id)
        .order_by("pdf_order", "field_label", "usage_key")
    )
