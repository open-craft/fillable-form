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

    def test_indexes_display_name_and_instructions(self, block):
        """display_name and instructions are indexed under 'content'."""
        block.display_name = "My Form Field"
        block.instructions = "Fill this in"

        result = block.index_dictionary()

        assert result["content_type"] == "Fillable Form"
        assert result["content"]["display_name"] == "My Form Field"
        assert result["content"]["instructions"] == "Fill this in"

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
        """field_label, form_group_id, show_download_button, pdf_order excluded."""
        block.field_label = "PDF Heading"
        block.form_group_id = "group-1"

        result = block.index_dictionary()

        assert "field_label" not in result["content"]
        assert "form_group_id" not in result["content"]
        assert "show_download_button" not in result["content"]
        assert "pdf_order" not in result["content"]

    def test_handles_none_instructions(self, block):
        """None instructions are indexed as an empty string."""
        block.instructions = None

        result = block.index_dictionary()

        assert result["content"]["instructions"] == ""


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
