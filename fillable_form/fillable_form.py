import html
import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.utils.text import slugify
from django.utils.translation import get_language, gettext as _
from webob.response import Response

from opaque_keys.edx.keys import CourseKey
import nh3
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

MATERIAL_ICONS_URL = "https://fonts.googleapis.com/icon?family=Material+Icons+Outlined"


def _strip_html(text: str) -> str:
    """Reduce HTML to searchable plain text; script/style contents are dropped."""
    text = (text or "").replace("<", " <")
    return " ".join(html.unescape(nh3.clean(text, tags=set())).split())


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
    icon = String(
        default="edit",
        scope=Scope.settings,
        help=_("Material Icons (outlined) name of the icon shown next to the title"),
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
    color_variant = String(
        default="",
        scope=Scope.settings,
        help=_(
            "Id of the colour variant applied to the block. "
            "When empty, the block uses its default colours."
        ),
    )
    download_button_info = String(
        default="",
        scope=Scope.settings,
        help=_(
            "Text shown in the download card next to the download button. "
            "When empty, the frontend shows its default text."
        ),
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

    @staticmethod
    def _xblock_react_config() -> dict[str, str]:
        """
        Config consumed by @opencraft/xblock-react-utils' createXBlockRoot,
        which uses it to load the Paragon theme into the block's shadow DOM.
        """
        return {
            "mfe_config_api": (
                f"{getattr(settings, 'LMS_ROOT_URL', '')}"
                "/api/mfe_config/v1?mfe=learning"
            ),
        }

    def _render_fragment(
        self,
        div_prefix: str,
        js_bundle: str,
        js_initializer: str,
        init_data: BaseModel,
        div_class: str = "",
    ) -> Fragment:
        """Build a Fragment that mounts a React bundle.
        """
        fragment = Fragment()
        # Font for the Material Icons; its CSS class is redefined in our
        # stylesheet because the page CSS does not reach the shadow DOM.
        fragment.add_resource_url(MATERIAL_ICONS_URL, "text/css", "head")
        class_attr = f' class="{div_class}"' if div_class else ""
        fragment.add_content(
            f'<div id="{div_prefix}-{self.scope_ids.usage_id}"{class_attr}></div>'
        )
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
            display_name=self.display_name,
            icon=self.icon,
            field_label=self.field_label,
            instructions=self.instructions,
            current_text=current_text,
            show_download_button=self.show_download_button,
            download_button_info=self.download_button_info,
            color_variant=self.color_variant,
            in_course_context=self._course_key() is not None,
            handler_urls={
                "save_response": self.runtime.handler_url(
                    self, "save_response"
                ),
                "download_pdf": self.runtime.handler_url(
                    self, "download_pdf"
                ),
            },
            locale=get_language(),
            config=self._xblock_react_config(),
        )

        return self._render_fragment(
            "fillable-form-learner",
            "static/js/fillable_form_learner.js",
            "FillableFormLearner",
            init_data,
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
        unit_names = self._get_unit_names(course_key, [field.usage_key for field in fields])

        form_data = FormGroupData(
            form_group_id=self.form_group_id,
            no_response_text=_("No response provided."),
            fields=[
                {
                    "field_label": f.field_label,
                    "instructions": f.instructions,
                    "response_text": response_map.get(str(f.usage_key), ""),
                    "unit_name": unit_names.get(str(f.usage_key), ""),
                }
                for f in fields
            ],
        )

        user_email = xblock_user.emails[0] if xblock_user and xblock_user.emails else ""
        user_name = self._resolve_user_name(xblock_user)

        # Fall back to the course key if CourseOverview is unavailable (outside
        # edx-platform) or has no entry for this course. The import is kept
        # separate from the lookup: if it fails, CourseOverview is unbound and
        # can't appear in an except clause.
        course_name = str(course_key)
        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
        except ImportError:
            pass
        else:
            try:
                course_name = CourseOverview.get_from_id(course_key).display_name
            except CourseOverview.DoesNotExist:
                pass

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

    @staticmethod
    def _get_unit_names(course_key: CourseKey, usage_keys: list[Any]) -> dict[str, str]:
        """Map each usage key to the display name of the unit that contains it.

        Fields whose unit can't be found (e.g. deleted blocks still in the registry)
        are left out. Outside edx-platform (no modulestore) the map is empty.
        """
        try:
            from xmodule.modulestore.django import modulestore
            from xmodule.modulestore.exceptions import ItemNotFoundError
        except ImportError:
            return {}

        store = modulestore()
        unit_names = {}
        # bulk_operations caches the course structure, so each lookup doesn't hit the database.
        with store.bulk_operations(course_key):
            for usage_key in usage_keys:
                try:
                    parent_key = store.get_parent_location(usage_key)
                    if parent_key:
                        unit_names[str(usage_key)] = store.get_item(parent_key).display_name_with_default
                except ItemNotFoundError:
                    continue
        return unit_names

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
            icon=self.icon,
            instructions=self.instructions,
            form_group_id=self.form_group_id,
            form_group_options=get_form_group_options(course_key) if course_key else [],
            field_label=self.field_label,
            show_download_button=self.show_download_button,
            download_button_info=self.download_button_info,
            color_variant=self.color_variant,
            pdf_order=self.pdf_order,
            handler_urls={
                "studio_submit": self.runtime.handler_url(
                    self, "studio_submit"
                ),
            },
            locale=get_language(),
            config=self._xblock_react_config(),
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
        self.icon = validated.icon
        self.instructions = validated.instructions
        self.form_group_id = validated.form_group_id
        self.field_label = validated.field_label
        self.show_download_button = validated.show_download_button
        if validated.download_button_info is not None:
            self.download_button_info = validated.download_button_info
        if validated.color_variant is not None:
            self.color_variant = validated.color_variant
        self.pdf_order = validated.pdf_order

        course_key = self._course_key()
        if course_key:
            # The form field registry only powers course-level form groups and
            # PDF assembly, so there is nothing to register outside a course.
            save_form_field(
                course_key=course_key,
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

    # Alias needed for client's "Data Bricks" indexer project.
    student_view_data = index_dictionary
