"""
Tests for XBlock handlers.

Run with: python -m pytest fillable_form/tests/test_handlers.py -v
"""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from opaque_keys.edx.keys import UsageKey


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
        block.instructions = "<p>Please fill this in.</p>"
        block.form_group_id = "group1"
        block.field_label = "Question 1"
        block.show_download_button = True
        block.pdf_order = 0

        return block


class TestStudentView:
    """Tests for student_view."""

    def test_student_view_renders_div(self, mock_block):
        """student_view() returns fragment with expected div and init data."""
        # Mock user services
        mock_block._get_django_user = Mock(return_value=(None, None))
        mock_block._is_legacy_studio = Mock(return_value=True)
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        fragment = mock_block.student_view()

        content = fragment.content
        assert "fillable-form-learner-" in content
        assert '<div id="fillable-form-learner-' in content
        mock_block.runtime.local_resource_url.assert_any_call(
            mock_block, "static/css/fillable_form.css"
        )

    def test_student_view_loads_existing_response(self, mock_block):
        """When FormResponse exists, student_view includes current_text."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))
        mock_block._is_legacy_studio = Mock(return_value=False)
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
        mock_block._is_legacy_studio = Mock(return_value=False)
        mock_block.runtime.handler_url = Mock(return_value="/handler/url")
        mock_block.runtime.local_resource_url = Mock(return_value="/static/url")

        with patch("fillable_form.fillable_form.get_response", return_value=""):
            fragment = mock_block.student_view()

        assert fragment is not None


class TestSaveResponseHandler:
    """Tests for save_response handler."""

    def test_save_response_creates(self, mock_block):
        """POST to save_response with new text creates FormResponse."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with patch("fillable_form.fillable_form.save_response") as mock_save:
            mock_save.return_value = Mock(modified=Mock(isoformat=lambda: "2026-05-13T10:00:00"))
            result = mock_block.save_response({"response_text": "Hello"})

        assert result["success"] is True
        assert result["modified"] == "2026-05-13T10:00:00"

    def test_save_response_unauthenticated(self, mock_block):
        """Returns error when user not authenticated."""
        mock_block._get_django_user = Mock(return_value=(None, None))

        result = mock_block.save_response({"response_text": "Hello"})

        assert result["success"] is False
        assert "authenticated" in result["error"].lower()

    def test_save_response_invalid_payload(self, mock_block):
        """Returns error when fields missing."""
        mock_user = Mock(id=1)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with pytest.raises(Exception):
            mock_block.save_response({})  # missing response_text


class TestDownloadPdfHandler:
    """Tests for download_pdf handler."""

    def test_download_pdf_unauthenticated(self, mock_block):
        """Returns 404 when user not authenticated."""
        mock_block._get_django_user = Mock(return_value=(None, None))

        with pytest.raises(Exception):
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


class TestStudioView:
    """Tests for studio_view and studio_submit."""

    def test_studio_view_includes_form_group_options(self, mock_block):
        """studio_view() passes form_group_options in init data."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))
        mock_block._is_legacy_studio = Mock(return_value=False)
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
            result = mock_block.studio_submit({
                "display_name": "New Name",
                "instructions": "<p>New Instr</p>",
                "form_group_id": "group2",
                "field_label": "Q2",
                "show_download_button": True,
                "pdf_order": 20,
            })

        assert result["success"] is True
        assert mock_block.display_name == "New Name"
        assert mock_block.instructions == "<p>New Instr</p>"
        assert mock_block.form_group_id == "group2"
        assert mock_block.field_label == "Q2"
        assert mock_block.show_download_button is True
        assert mock_block.pdf_order == 20
        mock_upsert.assert_called_once()

    def test_studio_submit_permission_denied(self, mock_block):
        """Returns permission denied when user is not staff."""
        mock_user = Mock(id=1, is_staff=False)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        result = mock_block.studio_submit({
            "display_name": "X",
            "instructions": "X",
            "form_group_id": "X",
            "field_label": "X",
            "show_download_button": False,
            "pdf_order": 0,
        })

        assert result["success"] is False
        assert "permission" in result["error"].lower()

    def test_studio_submit_invalid_payload(self, mock_block):
        """Returns error when required fields missing."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        with pytest.raises(Exception):
            mock_block.studio_submit({})  # missing all fields

    def test_studio_submit_preserves_instructions_html(self, mock_block):
        """HTML in instructions is stored as-is."""
        mock_user = Mock(id=1, is_staff=True)
        mock_block._get_django_user = Mock(return_value=(mock_user, None))

        html = "<p><strong>Bold</strong> instructions</p>"
        with patch("fillable_form.fillable_form.save_form_field"):
            result = mock_block.studio_submit({
                "display_name": "X",
                "instructions": html,
                "form_group_id": "X",
                "field_label": "X",
                "show_download_button": False,
                "pdf_order": 0,
            })

        assert result["success"] is True
        assert mock_block.instructions == html
