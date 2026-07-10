# 5-Day Build Plan — CareerVerse AI MVP

Goal: a working end-to-end flow (not every feature deep, but every step of the journey functional) by end of Day 5.

Rule for all 5 days: **build with dummy/mock data first, wire real AI/DB last on each feature.** This keeps you unblocked if an integration takes longer than expected.

---

## Day 1 — Foundation + Landing + Skeleton Auth

**Goal:** Project scaffolded, running locally, deployable from commit #1.

- [ ] Create folder structure (frontend/, backend/, docs/, etc. per README)
- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] Install Tailwind + shadcn/ui + Framer Motion
- [ ] FastAPI backend skeleton (`main.py`, health check route)
- [ ] PostgreSQL schema v1: `users`, `resumes`, `job_descriptions`, `reports`
- [ ] Simple JWT auth (signup/login) — skip Clerk for now
- [ ] Landing page (hero, CTA, nav) — this is your "visible progress" win
- [ ] Deploy skeleton to Vercel + Render (deploy early, deploy often)

**End of day check:** You can sign up, log in, and see a live landing page on a real URL.

---

## Day 2 — Resume Upload + Parsing + Resume Report

**Goal:** Upload a resume → get a real AI-generated review.

- [ ] Upload Resume page (drag-drop UI, dummy "uploading..." state first)
- [ ] Supabase Storage integration for PDF upload
- [ ] PyMuPDF text extraction service
- [ ] Resume Reviewer Agent — first real OpenAI call, prompt in `backend/app/prompts/resume_reviewer.py`
- [ ] Resume Report page — render AI output (strengths, weaknesses, ATS score, suggestions)
- [ ] Store parsed resume + report in Postgres

**End of day check:** Real resume in → real AI-generated report out, persisted to DB.

---

## Day 3 — Job Descriptions + RAG + Top 3 Matches + Simulations

**Goal:** Upload JDs, retrieve the top 3 matching jobs, simulate all 3 so the user can compare.

- [ ] Upload Job Description page (multi-file upload)
- [ ] Chunk + embed JDs with `text-embedding-3-small`
- [ ] Store embeddings in local ChromaDB
- [ ] Retrieval function: given resume embedding, return top-k matching JD chunks
- [ ] Career Advisor Agent — takes resume + retrieved JD chunks → returns **top 3 matched jobs** with match % + reasoning each (full matched JD text stored per match for reuse by later agents)
- [ ] Top 3 Matches page (3 cards, match %, why-it-fits)
- [ ] Job Simulation Agent — runs once per matched job (3 times total), each grounded in that specific job's real JD text: 3-4 decision points drawn from actual responsibilities listed in that JD (not a generic template — e.g. if the JD mentions "client presentations," a decision point should involve one)
- [ ] Job Simulations page (tabbed or carousel — one simulation per matched job) with a "choose this one as my target" button on each

**End of day check:** Upload a JD set, get 3 clearly-identified matches, each with its own distinct simulation grounded in its own JD content (this is your RAG proof point — don't skip it, it's the technical differentiator). User can pick one as their target job.

---

## Day 4 — Skill Gap + Interview Coach (grounded in the chosen job)

**Goal:** Everything today is generated *from the chosen job's actual JD*, not generically.

- [ ] Resume vs chosen-JD side-by-side comparison view
- [ ] Skill Gap Agent — missing skills specific to the chosen job + roadmap
- [ ] Skill Gap page (gap chart + roadmap list)
- [ ] Interview Agent — questions specific to the chosen job's actual requirements
- [ ] Interview Coach page (question list, expandable answers)

**End of day check:** Full pipeline from resume → top 3 matches → 3 simulations → chosen job → gap → interview questions, and every downstream output clearly traces back to the *specific chosen* JD, not a generic role.

---

## Day 5 — Dashboard, Official Stretch Goal, Polish, Deploy

**Goal:** Ship it, and if on schedule, add the official stretch goal.

- [ ] Final Dashboard page — pulls together resume score, chosen job, skill gap summary, and a recap of all 3 simulations tried
- [ ] **Official stretch goal:** extend Skill Gap Agent output into a 3-month learning plan (Month 1/2/3, topics + resources) targeting the chosen job's missing skills — cheap to add since it reuses Skill Gap Agent data
- [ ] Loading states + error handling across all pages (uploads failing, AI timeouts — note: 3 simulations = 3 AI calls, add a "generating 3 simulations..." progress state, this step takes longer than others)
- [ ] Mobile responsiveness pass
- [ ] End-to-end manual test: fresh user, full journey, no dev tools open
- [ ] Fix critical bugs only — resist scope creep today
- [ ] Final deploy: frontend on Vercel, backend on Render, env vars set on both
- [ ] Write/update README with actual setup steps that worked
- [ ] Record a 2-minute demo video/GIF for the README or portfolio

**End of day check:** A stranger can open the deployed link, sign up, upload a resume, and get through the entire journey without you explaining anything.

---

## If you fall behind

Cut in this order (least to most painful):
1. 3-month learning plan → ship the flat skill gap roadmap only, add the month-by-month structure post-launch
2. Simulations for all 3 matches → simulate only the top 1 match, keep the other 2 as cards with just match %/reasoning (no simulation)
3. Skill Gap roadmap → shorten to a bullet list, skip visual chart
4. Multi-JD upload → support single JD only
5. Mobile polish → desktop-only for launch, fix mobile after

Do **not** cut: resume parsing, the RAG retrieval step that identifies the top matches, or the dashboard — those are what make this look like a real product instead of a form with GPT calls.
