"""Pydantic schemas and the SQLAlchemy `JobSimulation` model.

A `JobSimulation` stores the full AI-generated Virtual Work Experience (VWE)
for one `JobMatch`. Each experience is derived exclusively from the
`parsed_text` of the corresponding `JobDescription` — never from generic role
templates or hallucinated responsibilities. Three experiences are generated
concurrently (one per Top 3 career match) so the user can explore what each
role actually feels like before selecting one career path.

The `simulation_json` column holds the complete VWE content as returned and
validated by the Simulation Agent. The `SimulationContent` Pydantic model is
the schema for that JSON — Pydantic validates the AI output before it ever
reaches the database, so malformed agent output is rejected at the boundary.

-- What changed vs. the branching-decision format --
The previous format used `scenario_intro` and `decision_points` (a branching
path of options + consequences). This has been replaced with a Forage-style
task-based VWE: `overview` + `tasks`, where each task is an independent
workplace activity the user completes. The ORM model, read models, API
contract, concurrency strategy, and persistence logic are all unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy import JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# 0–10 inclusive — competency score range used on every task.
EvalScore = Annotated[int, Field(ge=0, le=10)]


# ---------------------------------------------------------------------------
# Competency evaluation (unchanged from branching format — same six criteria)
# ---------------------------------------------------------------------------


class TaskEvaluation(BaseModel):
    """Hidden competency scores for one completed task.

    Stored inside `simulation_json` and intentionally not surfaced to the
    user during the experience. These scores will power the Simulation
    Evaluation Agent in a later milestone.

    Scores reflect the level of competency the task exercises when answered
    correctly:
    - communication: clarity and effectiveness of written/verbal output.
    - problem_solving: quality of analytical or diagnostic reasoning.
    - technical_judgment: soundness of domain-specific decisions.
    - collaboration: ability to work across team or stakeholder boundaries.
    - leadership: initiative, ownership, and guiding others.
    - adaptability: flexibility when facing ambiguity or changing constraints.
    """

    communication: EvalScore
    problem_solving: EvalScore
    technical_judgment: EvalScore
    collaboration: EvalScore
    leadership: EvalScore
    adaptability: EvalScore


# ---------------------------------------------------------------------------
# Task sub-structures
# ---------------------------------------------------------------------------


class TaskResource(BaseModel):
    """A single reference document or artifact provided to the user for a task.

    Examples: Project Brief, Pull Request Diff, API Spec, Log File, Email Thread.
    """

    type: str = Field(min_length=1, description="Label for the resource, e.g. 'Project Brief'.")
    content: str = Field(min_length=1, description="Full text of the resource the user reads.")


class TaskActivity(BaseModel):
    """The actual work the user performs for a task.

    `type` determines how the frontend should render the activity:
    - multiple_choice — `options` lists 3–4 labelled choices (strings).
    - short_answer    — `options` is empty; user writes a free-text response.
    - prioritize      — `options` is a list of items to rank.
    - bug_analysis    — `options` is empty; user diagnoses a provided artefact.
    - email           — `options` is empty; user drafts an email.
    - report          — `options` is empty; user writes a short structured report.
    """

    type: str = Field(
        min_length=1,
        description=(
            "Activity type: multiple_choice | short_answer | prioritize | "
            "bug_analysis | email | report"
        ),
    )
    question: str = Field(min_length=1, description="The task prompt or question.")
    options: list[str] = Field(
        default_factory=list,
        description="Answer options for multiple_choice / prioritize tasks; empty otherwise.",
    )


class TaskFeedback(BaseModel):
    """Immediate per-task feedback shown to the user after they complete a task.

    Designed to deliver the educational value of the experience:
    - positive: what the user did well (or what the expected solution demonstrates).
    - improvement: one specific thing to do differently next time.
    - real_world_importance: why this task matters in actual practice.
    """

    positive: str = Field(min_length=1, description="What the user did well.")
    improvement: str = Field(min_length=1, description="One concrete improvement for next time.")
    real_world_importance: str = Field(
        min_length=1, description="Why this skill matters in the real workplace."
    )


class SimulationTask(BaseModel):
    """A single independent workplace task within a Virtual Work Experience.

    Tasks are numbered sequentially and progressively increase in difficulty,
    but each is self-contained — there is no branching narrative. Every task
    must trace to an explicit responsibility or requirement in the uploaded JD
    via `jd_reference`.
    """

    task_number: int = Field(ge=1, le=6, description="Sequential task number (1–6).")
    title: str = Field(min_length=1, description="Short task title, e.g. 'Review Pull Request'.")
    estimated_time: str = Field(
        min_length=1, description="Time estimate string, e.g. '5-10 mins'."
    )
    difficulty: str = Field(
        min_length=1, description="Difficulty label: 'Easy', 'Intermediate', or 'Hard'."
    )
    objective: str = Field(
        min_length=1, description="One sentence describing what the user will accomplish."
    )
    context: str = Field(
        min_length=1,
        description="2–3 sentences of scenario context that sets up the task.",
    )
    resources: list[TaskResource] = Field(
        default_factory=list,
        description="Reference materials the user reads before performing the activity.",
    )
    activity: TaskActivity
    expected_solution: str = Field(
        min_length=1,
        description="The correct or ideal answer/approach — shown after completion.",
    )
    feedback: TaskFeedback
    evaluation: TaskEvaluation
    jd_reference: str = Field(
        min_length=1,
        description=(
            "Verbatim or near-verbatim phrase from the uploaded JD that grounded this task."
        ),
    )


# ---------------------------------------------------------------------------
# Top-level VWE overview
# ---------------------------------------------------------------------------


class SimulationOverview(BaseModel):
    """Company, team, role, and project context shown on the first screen of the VWE."""

    company_context: str = Field(
        min_length=1, description="Brief description of the company inferred from the JD."
    )
    team_context: str = Field(
        min_length=1, description="Description of the team the user is joining."
    )
    your_role: str = Field(
        min_length=1, description="What the user's specific role and responsibilities are."
    )
    project_background: str = Field(
        min_length=1, description="The project or initiative the tasks are built around."
    )


# ---------------------------------------------------------------------------
# Root simulation content — replaces the old scenario_intro + decision_points
# ---------------------------------------------------------------------------


class SimulationContent(BaseModel):
    """Complete structured content of one AI-generated Virtual Work Experience.

    This is the schema stored as JSON in `JobSimulation.simulation_json`.
    The Simulation Agent must return a response that validates against this
    model — any deviation is rejected at the boundary before the database
    is touched.

    Fields
    ------
    job_title:          Role title from the matched JD.
    estimated_duration: Total time estimate for the VWE, e.g. '30-45 mins'.
    difficulty:         Overall difficulty label, e.g. 'Intermediate'.
    overview:           Company / team / role / project context.
    what_youll_learn:   3–5 learning outcomes for the user.
    what_youll_do:      3–5 bullet points describing the tasks at a glance.
    tasks:              4–6 independent workplace tasks, progressively harder.
    """

    job_title: str = Field(min_length=1)
    estimated_duration: str = Field(
        min_length=1, description="Total estimated duration, e.g. '30-45 mins'."
    )
    difficulty: str = Field(
        min_length=1, description="Overall difficulty: 'Beginner', 'Intermediate', or 'Advanced'."
    )
    overview: SimulationOverview
    what_youll_learn: list[str] = Field(
        min_length=3,
        max_length=5,
        description="3 to 5 learning outcomes.",
    )
    what_youll_do: list[str] = Field(
        min_length=3,
        max_length=5,
        description="3 to 5 high-level descriptions of what the tasks involve.",
    )
    tasks: list[SimulationTask] = Field(
        min_length=4,
        max_length=6,
        description="4 to 6 independent workplace tasks ordered by increasing difficulty.",
    )


# ---------------------------------------------------------------------------
# ORM model — UNCHANGED from the branching format
# ---------------------------------------------------------------------------


class JobSimulation(Base):
    """Persisted AI-generated Virtual Work Experience tied to one `JobMatch`.

    `simulation_json` stores the full validated `SimulationContent` dict.
    Load it back with `SimulationContent.model_validate(row.simulation_json)`.
    """

    __tablename__ = "job_simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_matches.id"),
        nullable=False,
        index=True,
    )
    simulation_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# API read model + response — UNCHANGED from the branching format
# ---------------------------------------------------------------------------


class JobSimulationRecord(BaseModel):
    """Read model for a persisted `JobSimulation` row — returned by the API.

    `simulation` is deserialized from `simulation_json` and validated against
    `SimulationContent` so the API consumer always receives a fully typed
    object. Use `from_orm_row()` to construct this from a `JobSimulation`
    ORM instance.
    """

    id: int
    job_match_id: int
    simulation: SimulationContent
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row: "JobSimulation") -> "JobSimulationRecord":
        """Construct from a `JobSimulation` ORM row.

        Parses and validates `simulation_json` into `SimulationContent` so
        callers never have to deal with raw dicts.
        """
        return cls(
            id=row.id,
            job_match_id=row.job_match_id,
            simulation=SimulationContent.model_validate(row.simulation_json),
            created_at=row.created_at,
        )


class SimulateAllResponse(BaseModel):
    """Returned by `POST /job-matches/{resume_id}/simulate-all`.

    Always contains exactly three `JobSimulationRecord`s, one per career
    match, ordered by `JobMatch.rank` (rank 1 = best match first).
    """

    simulations: list[JobSimulationRecord] = Field(
        min_length=3,
        max_length=3,
        description="One VWE per Top 3 career match, ordered by rank.",
    )
