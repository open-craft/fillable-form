from pydantic import BaseModel, Field


class LearnerInitData(BaseModel):
    """Init data passed to the learner React app."""
    block_id: str
    field_label: str
    instructions: str
    current_text: str
    show_download_button: bool
    handler_urls: dict[str, str]


class SaveResponseRequest(BaseModel):
    """Payload from the learner auto-save handler."""
    response_text: str


class StudioInitData(BaseModel):
    """Init data passed to the Studio React app."""
    block_id: str
    display_name: str
    instructions: str
    form_group_id: str
    form_group_options: list[str] = Field(default_factory=list)
    field_label: str
    show_download_button: bool
    pdf_order: int = 0
    handler_urls: dict[str, str]


class StudioSaveData(BaseModel):
    """Payload from the Studio editor submit handler."""
    display_name: str
    instructions: str
    form_group_id: str
    field_label: str
    show_download_button: bool
    pdf_order: int = Field(ge=0)
