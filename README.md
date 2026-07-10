# CareerVerse AI — AI Resume & Career Advisor

> Status: 🚧 In active development — 5-day MVP sprint. See [WORKFLOW.md](./WORKFLOW.md) for the day-by-day build plan.

## Problem

Students struggle to tailor resumes for specific job roles. They don't know how their resume actually stacks up against real job postings, what skills they're missing, or what it would actually feel like to work in the roles their resume qualifies them for.

## Core Idea

Upload a resume → AI analyzes it and scores it → RAG retrieves matching job descriptions from uploaded JD PDFs → the **top 3 most relevant jobs** are identified → **each of the 3 gets its own job simulation** (a day in that specific role, grounded in its real JD content — not generic) so the user can actually compare what each job would feel like → user picks one as their target → deep skill gap, interview prep, and 3-month plan are generated for that chosen job.

---

## Features (per spec)

**Prompt Engineering**
- Resume analysis
- Skill gap identification

**RAG**
- Retrieve job descriptions from uploaded PDFs

**Agent**
- Resume Reviewer Agent
- Career Advisor Agent

**Output**
- Resume score
- Missing skills
- Interview preparation roadmap

**Stretch Goal (official)**
- Generate a personalized 3-month learning plan

**Additional stretch features** (added on top, see below) — Chat with Resume, AI Resume Rewriter, Dark Mode, Shareable Public Report, Branded PDF Export.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite | Fast dev loop, type safety |
| Styling | Tailwind CSS + shadcn/ui | Premium look, fast to build |
| Animation | Framer Motion | Polish without custom CSS |
| Backend | FastAPI | Python-native, easy AI library integration |
| AI | OpenAI GPT-4.1 / GPT-4o | Reasoning + agent orchestration |
| Embeddings | text-embedding-3-small | Cheap, fast, good enough for MVP |
| Vector DB | ChromaDB (local) | Zero-ops, migrate to cloud later |
| Database | PostgreSQL | Users, resumes, reports, simulations |
| Auth | Simple JWT (MVP) → Clerk (post-MVP) | Ship faster; swap in later |
| File Storage | Supabase Storage | Resume/JD PDFs |
| PDF Parsing | PyMuPDF | Reliable text extraction |
| Deployment | Vercel (frontend) + Render (backend) | Free tier, zero-config CI |

---

## Architecture

```
CareerVerse AI
│
├── Frontend (React)
├── Backend (FastAPI)
├── AI Layer (OpenAI + Agents)
├── RAG (ChromaDB)
├── Database (PostgreSQL)
└── Deployment (Vercel + Render)
```

### AI Agent Pipeline

```
Resume Reviewer Agent
        ↓
Career Advisor Agent  (identifies TOP 3 relevant jobs from RAG results)
        ↓
Job Simulation Agent  (runs once per matched job → 3 simulations, one per match)
        ↓
   [ user compares all 3 simulations, picks ONE target job ]
        ↓
Skill Gap Agent  (resume vs the chosen job's actual requirements)
        ↓
Interview Agent  (questions specific to the chosen job)
```

Each agent = its own prompt file under `backend/app/prompts/`, called independently so they can be tested and improved in isolation. The Career Advisor Agent's top 3 picks are the thread every downstream agent depends on: all 3 get simulated so the user can compare, but skill gap / interview / learning plan only run once — for whichever job the user actually chooses — to keep AI cost and scope sane.

---

## User Journey

```
Landing → Login → Upload Resume → Parsing → Resume Analysis (score)
   → Upload Job Description(s) → RAG Retrieval → Top 3 Relevant Jobs identified
   → Job Simulations (all 3, side-by-side/tabbed) → user picks ONE target job
   → Skill Gap (vs chosen job) → Interview Prep (for chosen job) → Final Dashboard
```

---

## Folder Structure

```
careerverse-ai/
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       └── lib/
├── backend/
│   └── app/
│       ├── api/          # route handlers
│       ├── models/       # pydantic + db models
│       ├── services/     # business logic
│       ├── agents/       # AI agent orchestration
│       ├── rag/          # embedding + retrieval logic
│       ├── prompts/       # per-agent prompt templates
│       ├── utils/
│       └── main.py
├── docs/
├── data/
├── uploads/
├── vector_db/
├── tests/
├── README.md
└── WORKFLOW.md
```

---

## Screens (MVP scope)

1. Landing Page
2. Login
3. Dashboard
4. Upload Resume
5. Resume Report (score + strengths/weaknesses)
6. Upload Job Description
7. Top 3 Matches (RAG's top 3 picks, each with match % + reasoning)
8. Job Simulations (tabbed/carousel — a day in each of the 3 matched jobs, then a "choose this one" action)
9. Skill Gap (missing skills vs the chosen job)
10. Interview Coach (questions for the chosen job)
11. Final Report (score, missing skills, interview roadmap)

## Official Stretch Goal — 3-Month Learning Plan

Extends the Skill Gap Agent's output into a month-by-month plan (Month 1 / Month 2 / Month 3, each with topics + suggested resources) targeting the missing skills for the *chosen* job specifically. Low extra effort since it reuses the Skill Gap Agent's data — do this before the "additional stretch features" below if time is tight, since it's the one actually in the spec.

## Additional Stretch Features (Day 6-7, if core + official stretch goal ship on time)

See [STRETCH_FEATURES.md](./STRETCH_FEATURES.md) for exact Cursor prompts.

- **Chat with your Resume** — RAG chatbot answering questions grounded in the user's own resume
- **AI Resume Rewriter** — inline, accept/reject suggestions to strengthen weak bullet points
- **Dark Mode** — full theme toggle with polished micro-animations throughout
- **Shareable Public Report** — read-only public link for the final report, portfolio-ready
- **Branded PDF Export** — downloadable PDF of the final report

---

## Local Setup

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Environment Variables
Create `.env` in `backend/`:
```
OPENAI_API_KEY=
DATABASE_URL=
SUPABASE_URL=
SUPABASE_KEY=
JWT_SECRET=
```

---

## Deployment

- **Frontend** → Vercel (auto-deploy on push to `main`)
- **Backend** → Render (Docker or native Python service)
- **Database** → Render PostgreSQL or Supabase Postgres
- **Vector DB** → ChromaDB persisted to disk in MVP; migrate to hosted vector DB post-launch

---

## Roadmap (post-MVP)

- Swap simple auth → Clerk
- Deepen Career Simulation Agent (branching scenarios)
- Move ChromaDB → hosted vector DB (Pinecone/Weaviate)
- Multi-resume comparison
- Team/recruiter view
