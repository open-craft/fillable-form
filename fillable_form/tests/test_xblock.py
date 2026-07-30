"""
Tests for XBlock defaults and structure.

Run with: python -m pytest fillable_form/tests/test_xblock.py -v
"""
from unittest.mock import Mock, patch

import pytest
from opaque_keys.edx.keys import UsageKey
from xblock.field_data import DictFieldData


@pytest.fixture
def block():
    """Create a FillableFormXBlock with minimal mocking."""
    with patch("fillable_form.fillable_form.settings"):
        from fillable_form.fillable_form import FillableFormXBlock

        return FillableFormXBlock(
            runtime=Mock(),
            scope_ids=Mock(usage_id=UsageKey.from_string(
                "block-v1:TestX+TS101+2026+type@fillable_form+block@testfield"
            )),
            field_data=DictFieldData({}),
        )


class TestXBlockDefaults:
    """Tests for default field values."""

    def test_display_name_default(self, block):
        """display_name defaults to 'Fillable Form Field'."""
        assert block.display_name == "Fillable Form Field"

    def test_instructions_default(self, block):
        """instructions defaults to empty string."""
        assert block.instructions == ""

    def test_form_group_id_default(self, block):
        """form_group_id defaults to empty string."""
        assert block.form_group_id == ""

    def test_field_label_default(self, block):
        """field_label defaults to empty string."""
        assert block.field_label == ""

    def test_show_download_button_default(self, block):
        """show_download_button defaults to False."""
        assert block.show_download_button is False

    def test_pdf_order_default(self, block):
        """pdf_order defaults to 0."""
        assert block.pdf_order == 0

    def test_fields_are_settings_scope(self, block):
        """All fields use Scope.settings."""
        assert block.fields["display_name"].scope == block.fields["instructions"].scope
        assert block.fields["form_group_id"].scope == block.fields["display_name"].scope


class TestIndexDictionary:
    """Tests for the index_dictionary Studio search (Meilisearch) payload."""

    def test_indexes_display_name_instructions_and_field_label(self, block):
        """display_name, instructions, and field_label are indexed under 'content'."""
        block.display_name = "My Form Field"
        block.instructions = "Fill this in"
        block.field_label = "Rating (1-5)"

        result = block.index_dictionary()

        assert result["content_type"] == "Fillable Form"
        assert result["content"]["display_name"] == "My Form Field"
        assert result["content"]["instructions"] == "Fill this in"
        assert result["content"]["field_label"] == "Rating (1-5)"

    def test_strips_html_from_instructions(self, block):
        """Rich-text HTML markup is stripped from indexed instructions."""
        block.instructions = "<p>Describe your <strong>goals</strong></p>"

        result = block.index_dictionary()

        instructions = result["content"]["instructions"]
        assert "<" not in instructions
        assert ">" not in instructions
        assert "Describe your" in instructions
        assert "goals" in instructions

    def test_excludes_non_searchable_fields(self, block):
        """form_group_id, show_download_button, pdf_order excluded."""
        block.form_group_id = "group-1"

        result = block.index_dictionary()

        assert "form_group_id" not in result["content"]
        assert "show_download_button" not in result["content"]
        assert "pdf_order" not in result["content"]

    def test_handles_none_instructions(self, block):
        """None instructions and field_label are indexed as empty strings."""
        block.instructions = None
        block.field_label = None

        result = block.index_dictionary()

        assert result["content"]["instructions"] == ""
        assert result["content"]["field_label"] == ""


class TestHelpers:
    """Tests for helper methods."""

    def test_is_legacy_studio_true(self, block):
        """_is_legacy_studio returns True when MFE is disabled."""
        with patch("fillable_form.fillable_form.settings") as mock_settings:
            mock_settings.ENABLE_STUDIO_MFE = False
            assert block._is_legacy_studio() is True

    def test_is_legacy_studio_false(self, block):
        """_is_legacy_studio returns False when MFE is enabled."""
        with patch("fillable_form.fillable_form.settings") as mock_settings:
            mock_settings.ENABLE_STUDIO_MFE = True
            assert block._is_legacy_studio() is False

    def test_get_django_user_no_xblock_user(self, block):
        """Returns None when no XBlock user service available."""
        mock_user_service = Mock()
        mock_user_service.get_current_user.return_value = None
        block.runtime.service.return_value = mock_user_service

        result = block._get_django_user()
        assert result == (None, None)

    def test_get_django_user_authenticated(self, block):
        """Returns Django user when authenticated."""
        mock_xblock_user = Mock()
        mock_xblock_user.opt_attrs = {"edx-platform.user_id": 1}

        mock_user_service = Mock()
        mock_user_service.get_current_user.return_value = mock_xblock_user
        block.runtime.service.return_value = mock_user_service

        with patch("fillable_form.fillable_form.User") as mock_user_model:
            mock_user = Mock(id=1)
            mock_user_model.objects.get.return_value = mock_user

            result = block._get_django_user()
            assert result[0] == mock_user


@pytest.fixture
def library_block():
    """Create a FillableFormXBlock with a content-library usage key."""
    with patch("fillable_form.fillable_form.settings"):
        from fillable_form.fillable_form import FillableFormXBlock

        runtime = Mock()
        runtime.handler_url.return_value = "/handler/studio_submit"
        return FillableFormXBlock(
            runtime=runtime,
            scope_ids=Mock(usage_id=UsageKey.from_string(
                "lb:TestX:wgu-xblocks:fillable_form:libtest"
            )),
            field_data=DictFieldData({}),
        )


class TestLibraryContext:
    """The block degrades gracefully outside a course (e.g. content libraries)."""

    def test_studio_view_renders_with_empty_form_groups(self, library_block):
        """studio_view must not crash in a library; form groups are unavailable."""
        with patch("fillable_form.fillable_form.get_form_group_options") as get_options:
            fragment = library_block.studio_view()

        get_options.assert_not_called()
        assert fragment.content

    def test_save_response_returns_error(self, library_block):
        """Saving a response outside a course fails cleanly instead of raising."""
        from fillable_form.fillable_form import FillableFormXBlock

        with patch.object(library_block, "_get_django_user", return_value=(Mock(id=1), None)):
            result = FillableFormXBlock.save_response.__wrapped__(
                library_block, {"response_text": "hi"}
            )

        assert result["success"] is False
        assert "course" in result["error"]

    def test_download_pdf_raises_http404(self, library_block):
        """PDF download outside a course raises Http404 instead of crashing."""
        from django.http import Http404

        with patch.object(library_block, "_get_django_user", return_value=(Mock(id=1), None)):
            with pytest.raises(Http404):
                library_block.download_pdf(request=Mock())

    def test_studio_submit_saves_without_registry(self, library_block):
        """Saving the editor in a library updates fields but skips the course registry."""
        from fillable_form.fillable_form import FillableFormXBlock

        payload = {
            "display_name": "Library Form",
            "instructions": "<p>Fill this in</p>",
            "form_group_id": "",
            "field_label": "Answer",
            "show_download_button": False,
            "pdf_order": 0,
        }
        with patch.object(library_block, "_get_django_user", return_value=(Mock(id=1), None)):
            with patch("fillable_form.fillable_form.save_form_field") as save_field:
                result = FillableFormXBlock.studio_submit.__wrapped__(library_block, payload)

        assert result["success"] is True
        save_field.assert_not_called()
        assert library_block.display_name == "Library Form"
        assert library_block.field_label == "Answer"

    def test_course_key_returns_course_key_in_courses(self, block):
        """Inside a course the helper returns the real CourseKey."""
        from opaque_keys.edx.keys import CourseKey

        assert isinstance(block._course_key(), CourseKey)  # pylint: disable=protected-access


def test_strip_html_hardening():
    """Script/style contents are dropped and markup edge cases are handled."""
    from fillable_form.fillable_form import _strip_html
    assert _strip_html('<script src="x.js">secret()</script>visible') == "visible"
    assert _strip_html("<style>.a{color:red}</style>styled") == "styled"
    assert _strip_html('<img alt="a > b">text') == "text"
    assert _strip_html("<p>foo</p><p>bar</p>") == "foo bar"
    assert _strip_html("see https://example.com <!-- hidden -->") == "see https://example.com"
    assert _strip_html(None) == ""
