from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.enums import IssueStatus


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


issue_labels = Table(
    "issue_labels",
    Base.metadata,
    Column("issue_id", ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("issue_id", "label_id", name="uq_issue_labels_pair"),
    Index("ix_issue_labels_issue_id", "issue_id"),
    Index("ix_issue_labels_label_id", "label_id"),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)

    issues: Mapped[list[Issue]] = relationship(back_populates="assignee")
    comments: Mapped[list[Comment]] = relationship(back_populates="author")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[IssueStatus] = mapped_column(Enum(IssueStatus, name="issue_status"), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    assignee: Mapped[User | None] = relationship(back_populates="issues")
    comments: Mapped[list[Comment]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    labels: Mapped[list[Label]] = relationship(
        secondary=issue_labels,
        back_populates="issues",
    )
    events: Mapped[list[IssueEvent]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_issues_status", "status"),
        Index("ix_issues_assignee_id", "assignee_id"),
        Index("ix_issues_created_at", "created_at"),
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")

    __table_args__ = (
        Index("ix_comments_issue_id", "issue_id"),
        Index("ix_comments_issue_id_created_at", "issue_id", "created_at"),
        CheckConstraint("length(trim(body)) > 0", name="ck_comments_body_nonempty"),
    )


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    issues: Mapped[list[Issue]] = relationship(
        secondary=issue_labels,
        back_populates="labels",
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_labels_name_nonempty"),
    )


class IssueEvent(Base):
    __tablename__ = "issue_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="events")
