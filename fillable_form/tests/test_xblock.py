"""
Tests for XBlock defaults and structure.

Run with: python -m pytest fillable_form/tests/test_xblock.py -v
"""
from unittest.mock import Mock, patch

import pytest
from opaque_keys.edx.keys import UsageKey


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
            field_data=Mock(),
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
        from django.contrib.auth import get_user_model

        mock_xblock_user = Mock()
        mock_xblock_user.opt_attrs = {"edx-platform.user_id": 1}

        mock_user_service = Mock()
        mock_user_service.get_current_user.return_value = mock_xblock_user
        block.runtime.service.return_value = mock_user_service

        with patch("fillable_form.fillable_form.get_user_model") as mock_gum:
            mock_user = Mock(id=1)
            mock_gum.return_value.objects.get.return_value = mock_user

            result = block._get_django_user()
            assert result[0] == mock_user
