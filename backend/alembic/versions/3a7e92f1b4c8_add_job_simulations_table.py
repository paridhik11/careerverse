"""add job_simulations table

Revision ID: 3a7e92f1b4c8
Revises: 1018824d317c
Create Date: 2026-07-11 20:00:00.000000

Adds the `job_simulations` table introduced by the AI Job Simulation Agent
milestone. Each row stores the full AI-generated workplace simulation JSON
for one `JobMatch`. Three simulations are generated concurrently — one per
Top 3 career match — so a single resume can have up to three simulation rows.

The `job_matches` table this references was created by the previous migration
(`1018824d317c_add_job_matches_table`). The `simulation_json` column is a
JSON blob containing the validated `SimulationContent` (see
`app.models.job_simulation`).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a7e92f1b4c8"
down_revision: str | Sequence[str] | None = "1018824d317c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_simulations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_match_id",
            sa.Integer(),
            sa.ForeignKey("job_matches.id"),
            nullable=False,
        ),
        sa.Column("simulation_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        op.f("ix_job_simulations_id"), "job_simulations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_job_simulations_job_match_id"),
        "job_simulations",
        ["job_match_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_job_simulations_job_match_id"), table_name="job_simulations")
    op.drop_index(op.f("ix_job_simulations_id"), table_name="job_simulations")
    op.drop_table("job_simulations")
