from datetime import datetime, timezone
from importlib.resources import files

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from weasyprint import CSS, HTML


class Info(BaseModel):
    title: str


class Student(BaseModel):
    email: str
    name: str


class Branding(BaseModel):
    logo: str = ""


class Metadata(BaseModel):
    info: Info
    student: Student
    branding: Branding = Field(default_factory=lambda: Branding(logo=""))


class FormFieldData(BaseModel):
    field_label: str
    instructions: str
    response_text: str


class FormGroupData(BaseModel):
    form_group_id: str
    fields: list[FormFieldData]

    def template_file(self) -> str:
        return "form_group.html"


_JINJA_ENV = Environment(
    loader=FileSystemLoader(
        files("fillable_form").joinpath("static/pdf/templates")
    ),
    autoescape=True,
)

_CACHED_CSS: str | None = None


def _get_css() -> str:
    global _CACHED_CSS
    if _CACHED_CSS is None:
        _CACHED_CSS = (
            files("fillable_form")
            .joinpath("static/pdf/base.css")
            .read_text(encoding="utf-8")
        )
    return _CACHED_CSS


def _render_html(metadata: Metadata, data: FormGroupData) -> str:
    """Render the form group data into HTML."""
    return _JINJA_ENV.get_template(data.template_file()).render(
        data=data.model_dump(),
        time=datetime.now(timezone.utc),
        **metadata.model_dump(),
    )


def generate_pdf(metadata: Metadata, data: FormGroupData) -> bytes:
    """Render the form group data into a PDF."""
    html = _render_html(metadata, data)

    return HTML(string=html).write_pdf(
        stylesheets=[CSS(string=_get_css())],
        pdf_variant="pdf/a-3b",
    )
