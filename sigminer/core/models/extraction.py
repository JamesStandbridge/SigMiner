from typing import TypedDict

from pydantic import BaseModel


class MetaResponse(BaseModel):
    meta_name: str
    extracted_value: str | None
    confidence_score: float


class FieldConfig(TypedDict):
    field_name: str
    guideline: str
    can_be_overwritten: bool


class LauncherConfig(TypedDict):
    fields: list[FieldConfig]
    excluded_hosts: list[str]
    include_mode: bool
    file_path: str
    max_emails: int
    model: str
    exclusion_guideline: str | None
