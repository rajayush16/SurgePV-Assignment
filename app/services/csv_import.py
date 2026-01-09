import csv
from io import StringIO

from sqlalchemy.orm import Session

from app.crud.issues import apply_resolved_at
from app.crud.labels import get_or_create_labels
from app.crud.users import get_user_by_email
from app.enums import IssueStatus
from app.models import Issue
from app.services.timeline import log_event


REQUIRED_COLUMNS = {"title", "description", "status", "assignee_email", "labels"}


def _parse_labels(raw: str | None) -> list[str]:
    if not raw:
        return []
    labels: list[str] = []
    seen = set()
    for token in raw.split(";"):
        cleaned = token.strip()
        if not cleaned or cleaned in seen:
            continue
        labels.append(cleaned)
        seen.add(cleaned)
    return labels


def _parse_status(raw: str | None) -> IssueStatus | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    return IssueStatus(value)


def import_issues_from_csv(db: Session, content: str) -> dict:
    reader = csv.DictReader(StringIO(content))
    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        return {
            "total_rows": 0,
            "created": 0,
            "failed": 0,
            "errors": [{"row_number": 1, "reason": "Missing required columns"}],
        }

    rows = list(reader)
    errors: list[dict] = []
    parsed_rows: list[dict] = []

    for idx, row in enumerate(rows, start=2):
        title = (row.get("title") or "").strip()
        if not title:
            errors.append({"row_number": idx, "reason": "Title is required"})
            continue

        try:
            status = _parse_status(row.get("status"))
        except ValueError:
            errors.append({"row_number": idx, "reason": "Invalid status"})
            continue

        assignee_email = (row.get("assignee_email") or "").strip()
        assignee = None
        if assignee_email:
            assignee = get_user_by_email(db, assignee_email)
            if assignee is None:
                errors.append({"row_number": idx, "reason": "Assignee email not found"})
                continue

        labels = _parse_labels(row.get("labels"))
        parsed_rows.append(
            {
                "title": title,
                "description": (row.get("description") or "").strip() or None,
                "status": status or IssueStatus.open,
                "assignee_id": assignee.id if assignee else None,
                "labels": labels,
            }
        )

    if errors:
        return {
            "total_rows": len(rows),
            "created": 0,
            "failed": len(errors),
            "errors": errors,
        }

    created_count = 0
    for payload in parsed_rows:
        issue = Issue(
            title=payload["title"],
            description=payload["description"],
            status=payload["status"],
            assignee_id=payload["assignee_id"],
        )
        apply_resolved_at(issue, payload["status"])
        db.add(issue)
        db.flush()
        if payload["labels"]:
            labels = get_or_create_labels(db, payload["labels"])
            issue.labels = labels
        log_event(db, issue.id, "issue.created", {"status": issue.status, "assignee_id": issue.assignee_id})
        created_count += 1

    return {
        "total_rows": len(rows),
        "created": created_count,
        "failed": 0,
        "errors": [],
    }
