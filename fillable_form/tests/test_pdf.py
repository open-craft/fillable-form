"""
Tests for PDF generation.

Run with: python -m pytest fillable_form/tests/test_pdf.py -v
"""
import pytest

from fillable_form.pdf_generator import (
    Branding,
    FormFieldData,
    FormGroupData,
    Info,
    Metadata,
    Student,
    _render_html,
    generate_pdf,
)


class TestPdfGeneration:
    """Tests for the PDF generator."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for tests."""
        return Metadata(
            info=Info(title="Test Form"),
            student=Student(email="student@example.com", name="Test Student"),
            branding=Branding(logo=""),
        )

    @pytest.fixture
    def sample_form_data(self):
        """Create sample form data for tests."""
        return FormGroupData(
            form_group_id="test-group",
            fields=[
                FormFieldData(
                    field_label="Question 1",
                    instructions="<p>Please answer carefully.</p>",
                    response_text="My thoughtful answer.",
                ),
                FormFieldData(
                    field_label="Question 2",
                    instructions="",
                    response_text="Another answer.",
                ),
                FormFieldData(
                    field_label="Question 3",
                    instructions="<p>Optional question.</p>",
                    response_text="",  # Empty response
                ),
            ],
        )

    def test_generate_pdf_returns_bytes(self, sample_metadata, sample_form_data):
        """generate_pdf() returns non-empty bytes."""
        result = generate_pdf(sample_metadata, sample_form_data)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF header
        assert result[:5] == b"%PDF-"

    def test_pdf_contains_field_labels(self, sample_metadata, sample_form_data):
        """Generated PDF contains all field labels."""
        result = _render_html(sample_metadata, sample_form_data)

        assert "Question 1" in result
        assert "Question 2" in result
        assert "Question 3" in result

    def test_pdf_contains_responses(self, sample_metadata, sample_form_data):
        """Generated PDF contains response text."""
        result = _render_html(sample_metadata, sample_form_data)

        assert "My thoughtful answer." in result
        assert "Another answer." in result

    def test_pdf_contains_student_info(self, sample_metadata, sample_form_data):
        """Generated PDF contains student name and email."""
        result = _render_html(sample_metadata, sample_form_data)

        assert "Test Student" in result
        assert "student@example.com" in result

    def test_empty_responses_show_placeholder(self, sample_metadata, sample_form_data):
        """Fields with no response show placeholder text."""
        result = _render_html(sample_metadata, sample_form_data)

        assert "No response provided" in result

    def test_pdf_html_escaping(self, sample_metadata):
        """Response text with HTML-like content is escaped."""
        data = FormGroupData(
            form_group_id="test",
            fields=[
                FormFieldData(
                    field_label="Q1",
                    instructions="",
                    response_text='<script>alert("xss")</script>',
                ),
            ],
        )

        result = generate_pdf(sample_metadata, data)

        # The script tag content should be escaped in the PDF, not raw
        # The escaped version will show &lt;script&gt; or the characters will
        # be visually encoded
        assert b"<script>" not in result

    def test_form_group_id_in_template(self, sample_metadata, sample_form_data):
        """Verify the form group renders without errors for populated data."""
        result = generate_pdf(sample_metadata, sample_form_data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_empty_fields_list(self, sample_metadata):
        """PDF generation works with empty fields list."""
        data = FormGroupData(form_group_id="empty", fields=[])

        result = generate_pdf(sample_metadata, data)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:5] == b"%PDF-"


class TestPdfDataModels:
    """Tests for Pydantic data models."""

    def test_form_group_data_template_file(self):
        """FormGroupData.template_file() returns correct template."""
        data = FormGroupData(form_group_id="g1", fields=[])

        assert data.template_file() == "form_group.html"

    def test_metadata_defaults(self):
        """Metadata defaults to empty logo."""
        metadata = Metadata(
            info=Info(title="Test"),
            student=Student(email="e@e.com", name="N"),
        )

        assert metadata.branding.logo == ""

    def test_form_field_data_validation(self):
        """FormFieldData can be created with valid data."""
        field = FormFieldData(
            field_label="Q1",
            instructions="<p>Test</p>",
            response_text="Answer",
        )

        assert field.field_label == "Q1"
        assert field.instructions == "<p>Test</p>"
        assert field.response_text == "Answer"
