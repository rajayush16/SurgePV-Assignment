from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Label


def get_labels_by_names(db: Session, names: list[str]) -> list[Label]:
    if not names:
        return []
    return list(db.scalars(select(Label).where(Label.name.in_(names))))


def get_or_create_labels(db: Session, names: list[str]) -> list[Label]:
    if not names:
        return []
    existing = get_labels_by_names(db, names)
    existing_by_name = {label.name: label for label in existing}
    created: list[Label] = []
    for name in names:
        if name in existing_by_name:
            continue
        label = Label(name=name)
        db.add(label)
        created.append(label)
        existing_by_name[name] = label
    db.flush()
    return [existing_by_name[name] for name in names]
