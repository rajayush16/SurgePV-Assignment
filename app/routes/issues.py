from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.crud import comments as comment_crud
from app.crud import issues as issue_crud
from app.crud import labels as label_crud
from app.crud import users as user_crud
from app.db import get_db
from app.enums import IssueStatus
from app.errors import bad_request, conflict, not_found
from app.schemas import (
    BulkStatusRequest,
    BulkStatusResult,
    CommentCreate,
    CommentOut,
    CsvImportSummary,
    IssueCreate,
    IssueListResponse,
    IssueOut,
    IssueUpdate,
    LabelsUpdate,
)
from app.services.bulk_update import bulk_update_status
from app.services.csv_import import import_issues_from_csv
from app.services.timeline import get_timeline, log_event


router = APIRouter(prefix="/issues", tags=["issues"])


@router.post("", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, db: Session = Depends(get_db)) -> IssueOut:
    if payload.assignee_id is not None and user_crud.get_user(db, payload.assignee_id) is None:
        raise not_found("User", {"assignee_id": payload.assignee_id})
    issue = issue_crud.create_issue(db, payload.title, payload.description, payload.status, payload.assignee_id)
    log_event(db, issue.id, "issue.created", {"status": issue.status, "assignee_id": issue.assignee_id})
    db.commit()
    db.refresh(issue)
    return issue


@router.get("", response_model=IssueListResponse)
def list_issues(
    status: IssueStatus | None = None,
    assignee_id: int | None = None,
    label: str | None = None,
    limit: int = 20,
    offset: int = 0,
    sort: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db),
) -> IssueListResponse:
    items, total = issue_crud.list_issues(db, status, assignee_id, label, limit, offset, sort, order)
    return IssueListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db)) -> IssueOut:
    issue = issue_crud.get_issue(db, issue_id)
    if issue is None:
        raise not_found("Issue", {"issue_id": issue_id})
    return issue


@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(issue_id: int, payload: IssueUpdate, db: Session = Depends(get_db)) -> IssueOut:
    issue = issue_crud.get_issue(db, issue_id)
    if issue is None:
        raise not_found("Issue", {"issue_id": issue_id})
    if payload.version != issue.version:
        raise conflict("VERSION_CONFLICT", "Issue version mismatch", {"current_version": issue.version})

    updates: dict[str, Any] = {}
    for field in ("title", "description", "status", "assignee_id"):
        if field in payload.model_fields_set:
            updates[field] = getattr(payload, field)

    if "assignee_id" in updates and updates["assignee_id"] is not None:
        if user_crud.get_user(db, updates["assignee_id"]) is None:
            raise not_found("User", {"assignee_id": updates["assignee_id"]})

    issue_crud.update_issue(
        db,
        issue,
        updates.get("title"),
        updates.get("description"),
        updates.get("status"),
        updates.get("assignee_id") if "assignee_id" in updates else None,
    )
    log_event(db, issue.id, "issue.updated", updates)
    db.commit()
    db.refresh(issue)
    return issue


@router.post("/{issue_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(issue_id: int, payload: CommentCreate, db: Session = Depends(get_db)) -> CommentOut:
    issue = issue_crud.get_issue(db, issue_id)
    if issue is None:
        raise not_found("Issue", {"issue_id": issue_id})
    author = user_crud.get_user(db, payload.author_id)
    if author is None:
        raise not_found("User", {"author_id": payload.author_id})
    comment = comment_crud.create_comment(db, issue_id, payload.author_id, payload.body)
    log_event(db, issue.id, "comment.created", {"comment_id": comment.id})
    db.commit()
    db.refresh(comment)
    return comment


@router.put("/{issue_id}/labels", response_model=IssueOut)
def replace_labels(issue_id: int, payload: LabelsUpdate, db: Session = Depends(get_db)) -> IssueOut:
    issue = issue_crud.get_issue(db, issue_id)
    if issue is None:
        raise not_found("Issue", {"issue_id": issue_id})
    labels = label_crud.get_or_create_labels(db, payload.labels)
    issue.labels = labels
    log_event(db, issue.id, "labels.replaced", {"labels": payload.labels})
    db.commit()
    db.refresh(issue)
    return issue


@router.post("/bulk-status", response_model=BulkStatusResult)
def bulk_status(payload: BulkStatusRequest, db: Session = Depends(get_db)) -> BulkStatusResult:
    updated, errors = bulk_update_status(db, payload.issue_ids, payload.new_status)
    if errors:
        db.rollback()
        raise bad_request("BULK_STATUS_FAILED", "Bulk status update failed", {"errors": errors})
    log_event(db, payload.issue_ids[0], "bulk.status", {"issue_ids": payload.issue_ids, "status": payload.new_status})
    db.commit()
    return BulkStatusResult(updated=updated)


@router.post("/import", response_model=CsvImportSummary)
async def import_issues(file: UploadFile = File(...), db: Session = Depends(get_db)) -> CsvImportSummary:
    content = (await file.read()).decode("utf-8")
    summary = import_issues_from_csv(db, content)
    if summary["errors"]:
        db.rollback()
        return summary
    db.commit()
    return summary


@router.get("/{issue_id}/timeline")
def timeline(issue_id: int, db: Session = Depends(get_db)) -> list[dict]:
    issue = issue_crud.get_issue(db, issue_id)
    if issue is None:
        raise not_found("Issue", {"issue_id": issue_id})
    events = get_timeline(db, issue_id)
    return [event.__dict__ for event in events]
