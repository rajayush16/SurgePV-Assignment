from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import IssueStatus


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    author_id: int
    body: str
    created_at: datetime


class CommentCreate(BaseModel):
    body: str
    author_id: int

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Comment body cannot be empty")
        return value.strip()


class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LabelsUpdate(BaseModel):
    labels: list[str] = Field(default_factory=list)

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, value: list[str]) -> list[str]:
        cleaned = [label.strip() for label in value if label.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Duplicate labels are not allowed")
        return cleaned


class IssueBase(BaseModel):
    title: str
    description: str | None = None
    status: IssueStatus | None = None
    assignee_id: int | None = None


class IssueCreate(IssueBase):
    title: str
    status: IssueStatus | None = None


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None
    assignee_id: int | None = None
    version: int


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: IssueStatus
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    version: int
    labels: list[LabelOut]
    comments: list[CommentOut]


class IssueListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: IssueStatus
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    version: int
    labels: list[LabelOut]


class IssueListResponse(BaseModel):
    items: list[IssueListItem]
    total: int
    limit: int
    offset: int


class BulkStatusRequest(BaseModel):
    issue_ids: list[int]
    new_status: IssueStatus


class BulkStatusResult(BaseModel):
    updated: int


class CsvImportSummary(BaseModel):
    total_rows: int
    created: int
    failed: int
    errors: list[dict]


class TopAssigneeRow(BaseModel):
    assignee_id: int
    count: int


class TopAssigneesResponse(BaseModel):
    items: list[TopAssigneeRow]


class LatencyResponse(BaseModel):
    average_seconds: float | None
    resolved_count: int


class IssueEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    event_type: str
    payload: dict | None
    created_at: datetime
