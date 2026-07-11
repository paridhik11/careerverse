from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.job_descriptions import router as job_descriptions_router
from app.api.job_matches import router as job_matches_router
from app.api.job_simulations import router as job_simulations_router
from app.api.learning_roadmap import router as learning_roadmap_router
from app.api.resume import router as resume_router
from app.api.resume_review import router as resume_review_router
from app.api.skill_gap import router as skill_gap_router
from app.core.config import settings
from app.core.database import Base, engine
from app.models import job_description as _job_description_model  # noqa: F401 — registers JobDescription
from app.models import job_match as _job_match_model  # noqa: F401 — registers JobMatch on Base.metadata
from app.models import job_simulation as _job_simulation_model  # noqa: F401 — registers JobSimulation on Base.metadata
from app.models import learning_roadmap as _learning_roadmap_model  # noqa: F401 — registers LearningRoadmap on Base.metadata
from app.models import report as _report_model  # noqa: F401 — registers Report on Base.metadata
from app.models import resume as _resume_model  # noqa: F401 — registers Resume on Base.metadata
from app.models import skill_gap as _skill_gap_model  # noqa: F401 — registers SkillGap on Base.metadata
from app.models import user as _user_model  # noqa: F401 — registers User on Base.metadata

app = FastAPI(
    title="CareerVerse AI API",
    description="AI-powered career guidance platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP: create tables straight from ORM metadata (see the note in
# app.core.database for why this isn't Alembic yet).
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(resume_review_router)
app.include_router(job_descriptions_router)
app.include_router(job_matches_router)
app.include_router(job_simulations_router)
app.include_router(skill_gap_router)
app.include_router(learning_roadmap_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness probe for local development and deployment."""
    return {"status": "ok"}
