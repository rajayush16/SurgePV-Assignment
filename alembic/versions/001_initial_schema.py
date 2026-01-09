"""Initial schema.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-09 22:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    issue_status = postgresql.ENUM("OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", name="issue_status")
    issue_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
    )

    op.create_table(
        "labels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_labels_name_nonempty"),
    )

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum(name="issue_status"), nullable=False),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_index("ix_issues_status", "issues", ["status"])
    op.create_index("ix_issues_assignee_id", "issues", ["assignee_id"])
    op.create_index("ix_issues_created_at", "issues", ["created_at"])

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(body)) > 0", name="ck_comments_body_nonempty"),
    )
    op.create_index("ix_comments_issue_id", "comments", ["issue_id"])
    op.create_index("ix_comments_issue_id_created_at", "comments", ["issue_id", "created_at"])

    op.create_table(
        "issue_labels",
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("label_id", sa.Integer(), sa.ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("issue_id", "label_id", name="uq_issue_labels_pair"),
    )
    op.create_index("ix_issue_labels_issue_id", "issue_labels", ["issue_id"])
    op.create_index("ix_issue_labels_label_id", "issue_labels", ["label_id"])

    op.create_table(
        "issue_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("issue_events")
    op.drop_index("ix_issue_labels_label_id", table_name="issue_labels")
    op.drop_index("ix_issue_labels_issue_id", table_name="issue_labels")
    op.drop_table("issue_labels")
    op.drop_index("ix_comments_issue_id_created_at", table_name="comments")
    op.drop_index("ix_comments_issue_id", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_issues_created_at", table_name="issues")
    op.drop_index("ix_issues_assignee_id", table_name="issues")
    op.drop_index("ix_issues_status", table_name="issues")
    op.drop_table("issues")
    op.drop_table("labels")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS issue_status")
