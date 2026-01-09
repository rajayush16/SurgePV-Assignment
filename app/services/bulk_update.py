from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import IssueStatus
from app.models import Issue


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def bulk_update_status(
    db: Session, issue_ids: list[int], new_status: IssueStatus
) -> tuple[int, list[dict]]:
    errors: list[dict] = []
    if not issue_ids:
        return 0, errors

    issues = list(
        db.scalars(select(Issue).where(Issue.id.in_(issue_ids)).with_for_update())
    )
    issues_by_id = {issue.id: issue for issue in issues}
    missing = [issue_id for issue_id in issue_ids if issue_id not in issues_by_id]
    if missing:
        errors.append({"issue_ids": missing, "reason": "Issue not found"})
        return 0, errors

    for issue in issues:
        if new_status in (IssueStatus.resolved, IssueStatus.closed) and issue.assignee_id is None:
            errors.append({"issue_id": issue.id, "reason": "Assignee required for resolved/closed"})
        if new_status == IssueStatus.closed and issue.status == IssueStatus.open:
            errors.append({"issue_id": issue.id, "reason": "Cannot close directly from open"})

    if errors:
        return 0, errors

    now = _utcnow()
    for issue in issues:
        issue.status = new_status
        issue.updated_at = now
        if new_status in (IssueStatus.resolved, IssueStatus.closed):
            if issue.resolved_at is None:
                issue.resolved_at = now
        else:
            issue.resolved_at = None
        issue.version += 1
        db.add(issue)
    return len(issues), errors
