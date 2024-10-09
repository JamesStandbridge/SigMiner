from pydantic import BaseModel
from typing import TypedDict, List, Optional


class MetaResponse(BaseModel):
    meta_name: str
    extracted_value: Optional[str] 
    confidence_score: float


class FieldConfig(TypedDict):
    field_name: str
    guideline: str
    can_be_overwritten: bool


class LauncherConfig(TypedDict):
    fields: List[FieldConfig]
    excluded_hosts: List[str]
    include_mode: bool
    file_path: str
    max_emails: int
    model: str
