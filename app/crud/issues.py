from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.enums import IssueStatus
from app.models import Issue, Label, User, issue_labels


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def apply_resolved_at(issue: Issue, new_status: IssueStatus) -> None:
    if new_status in (IssueStatus.resolved, IssueStatus.closed):
        if issue.resolved_at is None:
            issue.resolved_at = _utcnow()
    else:
        issue.resolved_at = None


def create_issue(
    db: Session,
    title: str,
    description: str | None,
    status: IssueStatus | None,
    assignee_id: int | None,
) -> Issue:
    final_status = status or IssueStatus.open
    issue = Issue(
        title=title,
        description=description,
        status=final_status,
        assignee_id=assignee_id,
    )
    apply_resolved_at(issue, final_status)
    db.add(issue)
    db.flush()
    return issue


def get_issue(db: Session, issue_id: int) -> Issue | None:
    stmt = (
        select(Issue)
        .where(Issue.id == issue_id)
        .options(selectinload(Issue.labels), selectinload(Issue.comments))
    )
    return db.scalar(stmt)


def list_issues(
    db: Session,
    status: IssueStatus | None,
    assignee_id: int | None,
    label: str | None,
    limit: int,
    offset: int,
    sort: str,
    order: str,
) -> tuple[list[Issue], int]:
    stmt = select(Issue).options(selectinload(Issue.labels))
    if status:
        stmt = stmt.where(Issue.status == status)
    if assignee_id is not None:
        stmt = stmt.where(Issue.assignee_id == assignee_id)
    if label:
        stmt = stmt.join(issue_labels).join(Label).where(Label.name == label)

    total_stmt = select(func.count()).select_from(stmt.subquery())

    sort_col = Issue.created_at if sort == "created_at" else Issue.created_at
    if order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    stmt = stmt.limit(limit).offset(offset)
    items = list(db.scalars(stmt))
    total = db.scalar(total_stmt) or 0
    return items, total


def update_issue(
    db: Session,
    issue: Issue,
    title: str | None,
    description: str | None,
    status: IssueStatus | None,
    assignee_id: int | None,
) -> Issue:
    if title is not None:
        issue.title = title
    if description is not None:
        issue.description = description
    if status is not None:
        issue.status = status
        apply_resolved_at(issue, status)
    if assignee_id is not None or assignee_id is None:
        issue.assignee_id = assignee_id
    issue.updated_at = _utcnow()
    issue.version += 1
    db.add(issue)
    db.flush()
    return issue


def get_assignee(db: Session, assignee_id: int | None) -> User | None:
    if assignee_id is None:
        return None
    return db.get(User, assignee_id)
