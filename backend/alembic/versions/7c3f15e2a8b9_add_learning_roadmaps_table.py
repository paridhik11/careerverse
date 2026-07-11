"""add learning_roadmaps table

Revision ID: 7c3f15e2a8b9
Revises: 4b2d81e6c9a0
Create Date: 2026-07-11 23:00:00.000000

Adds the `learning_roadmaps` table introduced by the 3-Month Learning Roadmap
Agent milestone. Each row stores the AI-generated personalised 3-Month Learning
Roadmap for the single career the user has chosen after completing the Skill
Gap Analysis.

The roadmap is grounded in:
- The selected career's Job Description (primary source of truth).
- The Skill Gap Analysis for the chosen career (drives the progression).
- The candidate's resume (context on existing competencies).

The `skill_gaps` table this migration references was created by the previous
migration (`4b2d81e6c9a0_add_skill_gap_table`).

JSON column
-----------
- `roadmap_json` — dict: the full validated RoadmapContent
  {
    month_1: { focus, topics, projects, resources, milestones },
    month_2: { ... },
    month_3: { ... }
  }
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c3f15e2a8b9"
down_revision: str | Sequence[str] | None = "4b2d81e6c9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_roadmaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "resume_id",
            sa.Integer(),
            sa.ForeignKey("resumes.id"),
            nullable=False,
        ),
        sa.Column(
            "job_match_id",
            sa.Integer(),
            sa.ForeignKey("job_matches.id"),
            nullable=False,
        ),
        sa.Column("roadmap_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        op.f("ix_learning_roadmaps_id"), "learning_roadmaps", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_learning_roadmaps_resume_id"),
        "learning_roadmaps",
        ["resume_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_roadmaps_job_match_id"),
        "learning_roadmaps",
        ["job_match_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_learning_roadmaps_job_match_id"), table_name="learning_roadmaps"
    )
    op.drop_index(
        op.f("ix_learning_roadmaps_resume_id"), table_name="learning_roadmaps"
    )
    op.drop_index(op.f("ix_learning_roadmaps_id"), table_name="learning_roadmaps")
    op.drop_table("learning_roadmaps")
