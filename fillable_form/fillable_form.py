import logging
import re
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.utils.text import slugify
from django.utils.translation import get_language, gettext as _
from webob.response import Response

from opaque_keys.edx.keys import CourseKey
from pydantic import BaseModel
from xblock.core import XBlock
from xblock.fields import Boolean, Integer, String, Scope
from xblock.fragment import Fragment

User = get_user_model()

from .pdf_generator import (
    FormGroupData,
    Info,
    Metadata,
    Student,
    generate_pdf,
)
from .services import (
    get_form_group_options,
    get_form_group_responses,
    get_registered_form_fields,
    get_response,
    save_response,
    save_form_field,
)
from .types import (
    LearnerInitData,
    SaveResponseRequest,
    StudioInitData,
    StudioSaveData,
)

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    """Strip HTML tags from rich text, leaving plain text for search indexing."""
    return re.sub(r"<[^>]+>", " ", text)


@XBlock.wants("user")
class FillableFormXBlock(XBlock):
    """
    A fillable form field XBlock.

    Students fill in text fields placed at any point in a course.
    Responses across all fields in the same 'form group' can be
    aggregated and downloaded as a single PDF.
    """

    public_dir = "static"

    display_name = String(
        default=_("Fillable Form Field"),
        scope=Scope.settings,
        help=_("Display name for this component in Studio"),
    )
    instructions = String(
        default="",
        scope=Scope.settings,
        help=_("Rich-text instructions shown above the text area"),
    )
    form_group_id = String(
        default="",
        scope=Scope.settings,
        help=_(
            "Identifier that links fields together across the course. "
            "Fields with the same Form Group ID are aggregated in the "
            "downloaded PDF."
        ),
    )
    field_label = String(
        default="",
        scope=Scope.settings,
        help=_("Label used as the section heading for this field in the PDF"),
    )
    show_download_button = Boolean(
        default=False,
        scope=Scope.settings,
        help=_("When checked, a download button appears on this field"),
    )
    pdf_order = Integer(
        default=0,
        scope=Scope.settings,
        help=_("Lower numbers appear first in the downloaded PDF"),
    )

    def _get_xblock_user(self) -> Any:
        """Resolve the current user from the XBlock user service."""
        user_service = self.runtime.service(self, "user")
        return user_service.get_current_user()

    def _get_django_user(self) -> tuple[User | None, Any | None]:
        """
        Resolve the current user as a Django auth.User.

        Returns a tuple of (django_user, xblock_user) to avoid
        redundant resolution in callers that need both.
        """
        xblock_user = self._get_xblock_user()
        if not xblock_user:
            return None, None

        user_id = xblock_user.opt_attrs.get("edx-platform.user_id")
        if not user_id:
            return None, xblock_user

        try:
            return User.objects.get(id=user_id), xblock_user
        except User.DoesNotExist:
            return None, xblock_user

    @staticmethod
    def _resolve_user_name(xblock_user: Any) -> str:
        if not xblock_user:
            return _("Student")
        return (
            xblock_user.full_name
            or xblock_user.opt_attrs.get("edx-platform.username")
            or _("Student")
        )

    def _render_fragment(
        self,
        div_prefix: str,
        js_bundle: str,
        js_initializer: str,
        init_data: BaseModel,
        div_class: str = "",
        css_path: str | None = None,
    ) -> Fragment:
        """Build a Fragment with the standard CSS/JS loading pattern."""
        fragment = Fragment()
        class_attr = f' class="{div_class}"' if div_class else ""
        fragment.add_content(
            f'<div id="{div_prefix}-{self.scope_ids.usage_id}"{class_attr}></div>'
        )

        resolved_css_path = css_path or (
            "static/css/fillable_form_studio.css" if self._is_legacy_studio()
            else "static/css/fillable_form.css"
        )
        fragment.add_css_url(self.runtime.local_resource_url(self, resolved_css_path))
        fragment.add_javascript_url(
            self.runtime.local_resource_url(self, js_bundle)
        )
        fragment.initialize_js(js_initializer, init_data.model_dump(mode="json"))
        return fragment

    def student_view(self, context: dict[str, Any] | None = None) -> Fragment:
        """Render the student-facing fillable form field."""
        django_user, _xblock_user = self._get_django_user()

        current_text = ""
        if django_user:
            current_text = get_response(django_user, self.scope_ids.usage_id)

        init_data = LearnerInitData(
            block_id=str(self.scope_ids.usage_id),
            field_label=self.field_label,
            instructions=self.instructions,
            current_text=current_text,
            show_download_button=self.show_download_button,
            handler_urls={
                "save_response": self.runtime.handler_url(
                    self, "save_response"
                ),
                "download_pdf": self.runtime.handler_url(
                    self, "download_pdf"
                ),
            },
            locale=get_language(),
        )

        return self._render_fragment(
            "fillable-form-learner",
            "static/js/fillable_form_learner.js",
            "FillableFormLearner",
            init_data,
            css_path="static/css/fillable_form.css",
        )

    @XBlock.json_handler
    def save_response(self, data: dict[str, Any], suffix: str = "") -> dict[str, Any]:
        """Save a student's response text. Payload: {"response_text": "..."}."""
        request = SaveResponseRequest.model_validate(data)

        django_user, _xblock_user = self._get_django_user()
        if not django_user:
            return {"success": False, "error": _("User not authenticated.")}

        course_key = self._course_key()
        if not course_key:
            return {"success": False, "error": _("Responses can only be saved inside a course.")}

        response = save_response(
            user=django_user,
            course_key=course_key,
            usage_key=self.scope_ids.usage_id,
            form_group_id=self.form_group_id,
            response_text=request.response_text,
        )

        logger.debug(
            "Auto-saved response for user=%s usage=%s",
            django_user.id, self.scope_ids.usage_id,
        )

        return {
            "success": True,
            "modified": response.modified.isoformat(),
        }

    @XBlock.handler
    def download_pdf(self, request: Any, suffix: str = "") -> Response:
        """Generate and return a PDF of all responses in this field's form group."""
        django_user, xblock_user = self._get_django_user()
        if not django_user:
            raise Http404(_("User not authenticated."))

        course_key = self._course_key()
        if not course_key:
            raise Http404(_("PDF download is only available inside a course."))
        fields = list(get_registered_form_fields(course_key, self.form_group_id))
        response_map = get_form_group_responses(
            django_user, course_key, [field.usage_key for field in fields]
        )

        form_data = FormGroupData(
            form_group_id=self.form_group_id,
            no_response_text=_("No response provided."),
            fields=[
                {
                    "field_label": f.field_label,
                    "instructions": f.instructions,
                    "response_text": response_map.get(str(f.usage_key), ""),
                }
                for f in fields
            ],
        )

        user_email = xblock_user.emails[0] if xblock_user and xblock_user.emails else ""
        user_name = self._resolve_user_name(xblock_user)

        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
            course_name = CourseOverview.get_from_id(course_key).display_name
        except (ImportError, CourseOverview.DoesNotExist):
            course_name = str(course_key)

        metadata = Metadata(
            info=Info(title=self.display_name, course_name=course_name),
            student=Student(email=user_email, name=user_name),
        )

        pdf_bytes = generate_pdf(metadata, form_data)

        logger.info(
            "PDF downloaded: user=%s course=%s form_group=%s fields=%d",
            django_user.id, course_key, self.form_group_id, len(fields),
        )

        filename = slugify(f"{self.display_name}-{user_name}")
        return Response(
            pdf_bytes,
            content_type="application/pdf",
            content_disposition=f'attachment; filename="{filename}.pdf"',
        )

    def _course_key(self) -> CourseKey | None:
        """Return the containing course key, or None outside a course (e.g. content libraries)."""
        context_key = self.scope_ids.usage_id.context_key
        return context_key if isinstance(context_key, CourseKey) else None

    def studio_view(self, context: dict[str, Any] | None = None) -> Fragment:
        """Render the Studio editing interface."""
        course_key = self._course_key()

        init_data = StudioInitData(
            block_id=str(self.scope_ids.usage_id),
            display_name=self.display_name,
            instructions=self.instructions,
            form_group_id=self.form_group_id,
            form_group_options=get_form_group_options(course_key) if course_key else [],
            field_label=self.field_label,
            show_download_button=self.show_download_button,
            pdf_order=self.pdf_order,
            handler_urls={
                "studio_submit": self.runtime.handler_url(
                    self, "studio_submit"
                ),
            },
            locale=get_language(),
        )

        return self._render_fragment(
            "fillable-form-studio",
            "static/js/fillable_form_studio.js",
            "FillableFormStudio",
            init_data,
            div_class="editor-with-buttons",
        )

    @XBlock.json_handler
    def studio_submit(self, data: dict[str, Any], suffix: str = "") -> dict[str, Any]:
        """Save Studio editor form data."""
        django_user, _xblock_user = self._get_django_user()
        if not django_user:
            return {"success": False, "error": _("User not authenticated.")}

        validated = StudioSaveData.model_validate(data)

        self.display_name = validated.display_name
        self.instructions = validated.instructions
        self.form_group_id = validated.form_group_id
        self.field_label = validated.field_label
        self.show_download_button = validated.show_download_button
        self.pdf_order = validated.pdf_order

        save_form_field(
            course_key=self.scope_ids.usage_id.course_key,
            usage_key=self.scope_ids.usage_id,
            form_group_id=self.form_group_id,
            field_label=self.field_label,
            instructions=self.instructions,
            pdf_order=self.pdf_order,
        )

        logger.info(
            "Studio settings saved: user=%s block=%s",
            django_user.id, self.scope_ids.usage_id,
        )

        return {"success": True}

    def index_dictionary(self):
        """
        Return dictionary prepared with block content and type for indexing.
        """
        xblock_body = super().index_dictionary()
        index_body = {
            "display_name": self.display_name,
            "instructions": _strip_html(self.instructions or ""),
            "field_label": _strip_html(self.field_label or ""),
        }
        if "content" in xblock_body:
            xblock_body["content"].update(index_body)
        else:
            xblock_body["content"] = index_body
        xblock_body["content_type"] = "Fillable Form"
        return xblock_body

    @staticmethod
    def _is_legacy_studio() -> bool:
        """Detect whether we're rendering inside legacy Studio (not MFE)."""
        return not getattr(settings, "ENABLE_STUDIO_MFE", False)
