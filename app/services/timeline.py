from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IssueEvent


def log_event(db: Session, issue_id: int, event_type: str, payload: dict | None = None) -> IssueEvent:
    event = IssueEvent(issue_id=issue_id, event_type=event_type, payload=payload)
    db.add(event)
    db.flush()
    return event


def get_timeline(db: Session, issue_id: int) -> list[IssueEvent]:
    stmt = select(IssueEvent).where(IssueEvent.issue_id == issue_id).order_by(IssueEvent.created_at.asc())
    return list(db.scalars(stmt))
