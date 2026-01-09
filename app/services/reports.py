from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Issue


def top_assignees(db: Session, limit: int) -> list[dict]:
    stmt = (
        select(Issue.assignee_id, func.count(Issue.id).label("count"))
        .where(Issue.assignee_id.is_not(None))
        .group_by(Issue.assignee_id)
        .order_by(func.count(Issue.id).desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [{"assignee_id": row.assignee_id, "count": row.count} for row in rows]


def average_latency(db: Session) -> dict:
    diff_expr = func.extract("epoch", Issue.resolved_at - Issue.created_at)
    stmt = select(func.avg(diff_expr), func.count(Issue.id)).where(Issue.resolved_at.is_not(None))
    avg_value, count = db.execute(stmt).one()
    return {"average_seconds": float(avg_value) if avg_value is not None else None, "resolved_count": count}
