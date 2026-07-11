"""add skill_gap table

Revision ID: 4b2d81e6c9a0
Revises: 3a7e92f1b4c8
Create Date: 2026-07-11 22:00:00.000000

Adds the `skill_gaps` table introduced by the Skill Gap Analysis Agent
milestone. Each row stores the AI-generated personalised Skill Gap Analysis
for the single career the user has chosen after completing the Virtual Work
Experience (VWE).

The analysis is grounded exclusively in the selected career's uploaded Job
Description — skills are never reported unless they appear in the JD text.
Only one row is created per call (for the chosen career); the analysis is
NEVER run against the other two recommendations.

The `job_simulations` table this migration references was created by the
previous migration (`3a7e92f1b4c8_add_job_simulations_table`).

JSON columns
------------
- `existing_skills`            — list[str]: skills in both resume and JD
- `missing_technical_skills`   — list[str]: technical gaps from the JD
- `missing_soft_skills`        — list[str]: soft skill gaps from the JD
- `recommended_next_steps`     — list[str]: prioritised action items
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b2d81e6c9a0"
down_revision: str | Sequence[str] | None = "3a7e92f1b4c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skill_gaps",
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
        sa.Column("existing_skills", sa.JSON(), nullable=False),
        sa.Column("missing_technical_skills", sa.JSON(), nullable=False),
        sa.Column("missing_soft_skills", sa.JSON(), nullable=False),
        sa.Column("recommended_next_steps", sa.JSON(), nullable=False),
        sa.Column("readiness_score", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        op.f("ix_skill_gaps_id"), "skill_gaps", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_skill_gaps_resume_id"), "skill_gaps", ["resume_id"], unique=False
    )
    op.create_index(
        op.f("ix_skill_gaps_job_match_id"), "skill_gaps", ["job_match_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_skill_gaps_job_match_id"), table_name="skill_gaps")
    op.drop_index(op.f("ix_skill_gaps_resume_id"), table_name="skill_gaps")
    op.drop_index(op.f("ix_skill_gaps_id"), table_name="skill_gaps")
    op.drop_table("skill_gaps")
