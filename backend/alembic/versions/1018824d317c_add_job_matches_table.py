"""add job_matches table

Revision ID: 1018824d317c
Revises:
Create Date: 2026-07-11 00:00:00.000000

This is the first Alembic migration introduced into CareerVerse AI. The
`users`, `resumes`, `job_descriptions`, and `reports` tables that
`job_matches` references predate Alembic — per the MVP note in
`app.core.database`, they are created directly from ORM metadata via
`Base.metadata.create_all` in `app.main` at app startup. This migration only
adds the new `job_matches` table introduced by the Career Recommendation
Agent milestone, and assumes `resumes` and `job_descriptions` already exist.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1018824d317c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column(
            "job_description_id",
            sa.Integer(),
            sa.ForeignKey("job_descriptions.id"),
            nullable=False,
        ),
        sa.Column("role_title", sa.String(length=255), nullable=False),
        sa.Column("match_percent", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.String(length=16), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("career_overview", sa.Text(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column(
            "is_chosen", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        op.f("ix_job_matches_id"), "job_matches", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_job_matches_resume_id"), "job_matches", ["resume_id"], unique=False
    )
    op.create_index(
        op.f("ix_job_matches_job_description_id"),
        "job_matches",
        ["job_description_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_job_matches_job_description_id"), table_name="job_matches")
    op.drop_index(op.f("ix_job_matches_resume_id"), table_name="job_matches")
    op.drop_index(op.f("ix_job_matches_id"), table_name="job_matches")
    op.drop_table("job_matches")
