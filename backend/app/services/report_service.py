"""Persistence for `Report` records.

Kept generic on purpose: any agent (Resume Reviewer today, Career
Recommendation / Skill Gap / Roadmap later) can save its structured output
here by passing a `report_type` and a JSON-serializable `content` dict,
without needing its own table.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.report import Report


def save_report(db: Session, *, resume_id: int, report_type: str, content: dict) -> Report:
    """Persist an agent's structured output as a `Report` row tied to a resume."""
    report = Report(resume_id=resume_id, report_type=report_type, content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_latest_report(db: Session, *, resume_id: int, report_type: str) -> Report | None:
    """Fetch the most recently created report of `report_type` for a resume, or `None`.

    Used by later agents (e.g. Career Recommendation) that want the Resume
    Reviewer Agent's report as optional extra context without re-running it.
    """
    return (
        db.query(Report)
        .filter(Report.resume_id == resume_id, Report.report_type == report_type)
        .order_by(Report.created_at.desc())
        .first()
    )
