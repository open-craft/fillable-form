"""
Tests for XBlock handlers.

Run with: python -m pytest fillable_form/tests/test_handlers.py -v
"""
import json
import sys
import types
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.http import Http404
from opaque_keys.edx.keys import UsageKey
from pydantic import ValidationError
from webob import Request


def call_json_handler(handler, data):
    """POST ``data`` as JSON to an XBlock json_handler, as the runtime does, and decode the reply."""
    request = Request.blank("/", method="POST", body=json.dumps(data).encode("utf-8"))
    response = handler(request)
    return json.loads(response.body)


@pytest.fixture
def mock_block():
    """Create a mock FillableFormXBlock with required attributes."""
    with patch("fillable_form.fillable_form.settings"):
        from fillable_form.fillable_form import FillableFormXBlock

        block = FillableFormXBlock(
            runtime=Mock(),
            scope_ids=Mock(usage_id=UsageKey.from_string(
                "block-v1:TestX+TS101+2026+type@fillable_form+block@testfield"
            )),
            field_data=Mock(),
        )
        # Set up basic fields
        block.display_name = "Test Field"
        block.icon = "edit"
        block.instructions = "<p>Please fill this in.</p>"
        block.form_group_id = "group1"
        block.field_label = "Question 1"
        block.show_download_button = True
        block.download_button_info = "Download your answers as a PDF."
        block.color_variant = "default"
        block.pdf_order = 0

        return block


class TestStudentView:
    """Tests for student_view."""

    def test_student_view_renders_div(self, mock_block):
        """student_view() returns fragment with expected div and init data."""
        # Mock user services
        mock_block._get_django_user = Mock(return_value=(None, None))
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        fragment = mock_block.student_view()

        content = fragment.content
        assert "fillable-form-learner-" in content
        assert '<div id="fillable-form-learner-' in content
        # CSS is injected into the shadow DOM by the JS bundle, not linked.
        # Only the Material Icons font is linked.
        css_urls = [r.data for r in fragment.resources if r.mimetype == "text/css"]
        assert len(css_urls) == 1
        assert "Material+Icons+Outlined" in css_urls[0]
        mock_block.runtime.local_resource_url.assert_any_call(
            mock_block, "static/js/fillable_form_learner.js"
        )
        assert fragment.json_init_args["config"]["mfe_config_api"].endswith(
            "/api/mfe_config/v1?mfe=learning"
        )
        assert fragment.json_init_args["icon"] == "edit"
        assert fragment.json_init_args["download_button_info"] == (
            mock_block.download_button_info
        )
        assert fragment.json_init_args["color_variant"] == "default"

    def test_student_view_loads_existing_response(self, mock_block):
        """When FormResponse exists, student_view includes current_text."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        with patch("fillable_form.fillable_form.get_response", return_value="Existing text") as mock_get_response:
            fragment = mock_block.student_view()
            mock_get_response.assert_called_once_with(
                mock_user, mock_block.scope_ids.usage_id
            )

        assert fragment is not None

    def test_student_view_no_response(self, mock_block):
        """When no FormResponse, student_view includes empty current_text."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        with patch("fillable_form.fillable_form.get_response", return_value=""):
            fragment = mock_block.student_view()

        assert fragment is not None

    def test_student_view_flags_course_context(self, mock_block):
        """In a course, init data reports in_course_context=True."""
        mock_block._get_django_user = Mock(return_value=(None, None))
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        fragment = mock_block.student_view()

        assert fragment.json_init_args["in_course_context"] is True

    def test_student_view_flags_library_context(self, mock_block):
        """Outside a course (library preview), init data reports in_course_context=False."""
        from opaque_keys.edx.locator import LibraryUsageLocatorV2

        mock_block.scope_ids = Mock(usage_id=LibraryUsageLocatorV2.from_string(
            "lb:TestX:testlib:fillable_form:testfield"
        ))
        mock_block._get_django_user = Mock(return_value=(None, None))
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        fragment = mock_block.student_view()

        assert fragment.json_init_args["in_course_context"] is False


class TestSaveResponseHandler:
    """Tests for save_response handler."""

    def test_save_response_creates(self, mock_block):
        """POST to save_response with new text creates FormResponse."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with patch("fillable_form.fillable_form.save_response") as mock_save:
            mock_save.return_value = Mock(modified=Mock(isoformat=lambda: "2026-05-13T10:00:00"))
            result = call_json_handler(mock_block.save_response, {"response_text": "Hello"})

        assert result["success"] is True
        assert result["modified"] == "2026-05-13T10:00:00"

    def test_save_response_unauthenticated(self, mock_block):
        """Returns error when user not authenticated."""
        mock_block._get_django_user = Mock(return_value=(None, None))

        result = call_json_handler(mock_block.save_response, {"response_text": "Hello"})

        assert result["success"] is False
        assert "authenticated" in result["error"].lower()

    def test_save_response_invalid_payload(self, mock_block):
        """Rejects a payload with missing fields."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with pytest.raises(ValidationError):
            call_json_handler(mock_block.save_response, {})  # missing response_text


class TestDownloadPdfHandler:
    """Tests for download_pdf handler."""

    def test_download_pdf_unauthenticated(self, mock_block):
        """Returns 404 when user not authenticated."""
        mock_block._get_django_user = Mock(return_value=(None, None))

        with pytest.raises(Http404):
            mock_block.download_pdf(Mock())

    def test_download_pdf_returns_pdf(self, mock_block):
        """download_pdf() returns Response with content_type='application/pdf'."""
        mock_django_user = Mock(id=1)
        mock_xblock_user = Mock(emails=["test@example.com"], full_name="Test User")
        mock_xblock_user.opt_attrs = {"edx-platform.username": "testuser"}

        mock_block._get_django_user = Mock(return_value=(mock_django_user, mock_xblock_user))
        mock_block._get_xblock_user = Mock(return_value=mock_xblock_user)

        with patch("fillable_form.fillable_form.get_registered_form_fields") as mock_reg:
            with patch("fillable_form.fillable_form.get_form_group_responses") as mock_resp:
                with patch("fillable_form.fillable_form.generate_pdf") as mock_pdf:
                    mock_field = Mock(field_label="Q1", instructions="Do this", usage_key="block1")
                    mock_reg.return_value = [mock_field]
                    mock_resp.return_value = {"block1": "My answer"}
                    mock_pdf.return_value = b"%PDF-1.4 fake pdf"

                    result = mock_block.download_pdf(Mock())

        mock_resp.assert_called_once_with(
            mock_django_user,
            mock_block.scope_ids.usage_id.course_key,
            ["block1"],
        )
        assert result.content_type == "application/pdf"

    def test_download_pdf_includes_blank_for_unanswered_field(self, mock_block):
        """Registered unanswered fields are included with empty response text."""
        mock_django_user = Mock(id=1)
        mock_xblock_user = Mock(emails=[], full_name="Test User")
        mock_xblock_user.opt_attrs = {"edx-platform.username": "testuser"}
        mock_block._get_django_user = Mock(return_value=(mock_django_user, mock_xblock_user))

        fields = [
            Mock(field_label="Q1", instructions="Do this", usage_key="block1"),
            Mock(field_label="Q2", instructions="Do that", usage_key="block2"),
        ]

        with patch("fillable_form.fillable_form.get_registered_form_fields", return_value=fields):
            with patch("fillable_form.fillable_form.get_form_group_responses", return_value={"block1": "My answer"}):
                with patch("fillable_form.fillable_form.generate_pdf") as mock_pdf:
                    mock_pdf.return_value = b"%PDF-1.4 fake pdf"
                    mock_block.download_pdf(Mock())

        form_data = mock_pdf.call_args.args[1]
        assert form_data.fields[0].response_text == "My answer"
        assert form_data.fields[1].response_text == ""

    def test_download_pdf_includes_unit_names(self, mock_block):
        """Each field carries the name of its unit; unknown units get an empty name."""
        mock_django_user = Mock(id=1)
        mock_xblock_user = Mock(emails=[], full_name="Test User")
        mock_xblock_user.opt_attrs = {"edx-platform.username": "testuser"}
        mock_block._get_django_user = Mock(return_value=(mock_django_user, mock_xblock_user))
        mock_block._get_unit_names = Mock(return_value={"block1": "Unit 1"})

        fields = [
            Mock(field_label="Q1", instructions="", usage_key="block1"),
            Mock(field_label="Q2", instructions="", usage_key="block2"),
        ]

        with patch("fillable_form.fillable_form.get_registered_form_fields", return_value=fields):
            with patch("fillable_form.fillable_form.get_form_group_responses", return_value={}):
                with patch("fillable_form.fillable_form.generate_pdf") as mock_pdf:
                    mock_pdf.return_value = b"%PDF-1.4 fake pdf"
                    mock_block.download_pdf(Mock())

        form_data = mock_pdf.call_args.args[1]
        assert form_data.fields[0].unit_name == "Unit 1"
        assert form_data.fields[1].unit_name == ""

    def test_download_pdf_handles_empty_registry(self, mock_block):
        """Empty registry generates an empty form without falling back to course scan."""
        mock_django_user = Mock(id=1)
        mock_xblock_user = Mock(emails=[], full_name="Test User")
        mock_xblock_user.opt_attrs = {"edx-platform.username": "testuser"}
        mock_block._get_django_user = Mock(return_value=(mock_django_user, mock_xblock_user))

        with patch("fillable_form.fillable_form.get_registered_form_fields", return_value=[]):
            with patch("fillable_form.fillable_form.get_form_group_responses") as mock_resp:
                with patch("fillable_form.fillable_form.generate_pdf") as mock_pdf:
                    mock_pdf.return_value = b"%PDF-1.4 fake pdf"
                    mock_block.download_pdf(Mock())

        mock_resp.assert_called_once_with(
            mock_django_user,
            mock_block.scope_ids.usage_id.course_key,
            [],
        )
        form_data = mock_pdf.call_args.args[1]
        assert form_data.fields == []

    def test_download_pdf_falls_back_to_course_key_without_course_overview(self, mock_block):
        """Outside edx-platform (no CourseOverview), the course key is used as the course name."""
        mock_django_user = Mock(id=1)
        mock_xblock_user = Mock(emails=[], full_name="Test User")
        mock_xblock_user.opt_attrs = {"edx-platform.username": "testuser"}
        mock_block._get_django_user = Mock(return_value=(mock_django_user, mock_xblock_user))

        with patch("fillable_form.fillable_form.get_registered_form_fields", return_value=[]):
            with patch("fillable_form.fillable_form.get_form_group_responses", return_value={}):
                with patch("fillable_form.fillable_form.generate_pdf") as mock_pdf:
                    mock_pdf.return_value = b"%PDF-1.4 fake pdf"
                    mock_block.download_pdf(Mock())

        metadata = mock_pdf.call_args.args[0]
        assert metadata.info.course_name == str(mock_block.scope_ids.usage_id.course_key)


class TestGetUnitNames:
    """Tests for _get_unit_names, with a fake edx-platform modulestore."""

    @staticmethod
    def _fake_modulestore(parents, units):
        """Install fake xmodule modules; parents maps block -> unit key, units maps unit key -> name."""

        class ItemNotFoundError(Exception):
            pass

        def get_item(key):
            if key not in units:
                raise ItemNotFoundError(key)
            return Mock(display_name_with_default=units[key])

        store = MagicMock()
        store.get_parent_location.side_effect = parents.get
        store.get_item.side_effect = get_item

        modulestore_pkg = types.ModuleType("xmodule.modulestore")
        modulestore_pkg.__path__ = []
        django_mod = types.ModuleType("xmodule.modulestore.django")
        django_mod.modulestore = lambda: store
        exceptions_mod = types.ModuleType("xmodule.modulestore.exceptions")
        exceptions_mod.ItemNotFoundError = ItemNotFoundError
        return store, {
            "xmodule.modulestore": modulestore_pkg,
            "xmodule.modulestore.django": django_mod,
            "xmodule.modulestore.exceptions": exceptions_mod,
        }

    def test_maps_blocks_to_unit_names(self):
        """Returns the parent unit name per block and skips blocks without a unit."""
        from fillable_form.fillable_form import FillableFormXBlock

        store, modules = self._fake_modulestore(
            parents={"block1": "unit1", "block2": "unit2", "block3": "missing"},
            units={"unit1": "Unit One", "unit2": "Unit Two"},
        )
        with patch.dict(sys.modules, modules):
            result = FillableFormXBlock._get_unit_names(
                "course-v1:X+Y+Z", ["block1", "block2", "block3", "orphan"]
            )

        assert result == {"block1": "Unit One", "block2": "Unit Two"}
        store.bulk_operations.assert_called_once_with("course-v1:X+Y+Z")

    def test_returns_empty_without_modulestore(self):
        """Outside edx-platform there is no modulestore, so no unit names."""
        from fillable_form.fillable_form import FillableFormXBlock

        with patch.dict(sys.modules, {"xmodule.modulestore.exceptions": None}):
            assert FillableFormXBlock._get_unit_names("course-v1:X+Y+Z", ["block1"]) == {}


class TestStudioView:
    """Tests for studio_view and studio_submit."""

    def test_studio_view_mounts_in_shadow_dom(self, mock_block):
        """studio_view() links no CSS and passes the createXBlockRoot config."""
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        with patch("fillable_form.fillable_form.get_form_group_options", return_value=[]):
            fragment = mock_block.studio_view()

        # CSS is injected into the shadow DOM by the JS bundle, not linked.
        # Only the Material Icons font is linked.
        css_urls = [r.data for r in fragment.resources if r.mimetype == "text/css"]
        assert len(css_urls) == 1
        assert "Material+Icons+Outlined" in css_urls[0]
        assert fragment.json_init_args["config"]["mfe_config_api"].endswith(
            "/api/mfe_config/v1?mfe=learning"
        )

    def test_studio_view_includes_form_group_options(self, mock_block):
        """studio_view() passes form_group_options in init data."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        with patch("fillable_form.fillable_form.get_form_group_options", return_value=["g1", "g2"]):
            fragment = mock_block.studio_view()

        assert fragment is not None

    def test_studio_submit_saves_fields(self, mock_block):
        """studio_submit() persists all six fields and calls save_form_field."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with patch("fillable_form.fillable_form.save_form_field") as mock_upsert:
            result = call_json_handler(mock_block.studio_submit, {
                "display_name": "New Name",
                "icon": "edit",
                "instructions": "<p>New Instr</p>",
                "form_group_id": "group2",
                "field_label": "Q2",
                "show_download_button": True,
                "download_button_info": "Download all your answers.",
                "color_variant": "primary-navy",
                "pdf_order": 20,
            })

        assert result["success"] is True
        assert mock_block.display_name == "New Name"
        assert mock_block.instructions == "<p>New Instr</p>"
        assert mock_block.form_group_id == "group2"
        assert mock_block.field_label == "Q2"
        assert mock_block.show_download_button is True
        assert mock_block.download_button_info == "Download all your answers."
        assert mock_block.color_variant == "primary-navy"
        assert mock_block.pdf_order == 20
        mock_upsert.assert_called_once()

    def test_studio_submit_unauthenticated(self, mock_block):
        """Returns an error and saves nothing when the user isn't authenticated.

        Course-level write permission is enforced by Studio before the handler
        is reached, so the block itself only checks for an authenticated user.
        """
        mock_block._get_django_user = Mock(return_value=(None, None))

        with patch("fillable_form.fillable_form.save_form_field") as mock_upsert:
            result = call_json_handler(mock_block.studio_submit, {
                "display_name": "X",
                "icon": "edit",
                "instructions": "X",
                "form_group_id": "X",
                "field_label": "X",
                "show_download_button": False,
                "download_button_info": "",
                "color_variant": "default",
                "pdf_order": 0,
            })

        assert result["success"] is False
        assert "authenticated" in result["error"].lower()
        assert mock_block.display_name == "Test Field"
        mock_upsert.assert_not_called()

    def test_studio_submit_invalid_payload(self, mock_block):
        """Rejects a payload with missing fields."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with pytest.raises(ValidationError):
            call_json_handler(mock_block.studio_submit, {})  # missing all fields

    def test_studio_submit_preserves_instructions_html(self, mock_block):
        """HTML in instructions is stored as-is."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        html = "<p><strong>Bold</strong> instructions</p>"
        with patch("fillable_form.fillable_form.save_form_field"):
            result = call_json_handler(mock_block.studio_submit, {
                "display_name": "X",
                "icon": "edit",
                "instructions": html,
                "form_group_id": "X",
                "field_label": "X",
                "show_download_button": False,
                "download_button_info": "",
                "color_variant": "default",
                "pdf_order": 0,
            })

        assert result["success"] is True
        assert mock_block.instructions == html
