# Product Requirements Document (PRD)

# CareerVerse AI

Version: MVP v1.0

Status: In Development

---

# Vision

CareerVerse AI is an AI-powered career exploration platform that helps students understand which careers best match their skills by combining resume analysis, Retrieval-Augmented Generation (RAG), AI-powered career recommendations, interactive job simulations, and personalized learning guidance.

Instead of only telling students which career suits them, CareerVerse enables them to experience different career paths before making a decision.

> Experience the role before choosing your future.

---

# Problem Statement

Students often struggle to understand:

- Whether their resume is industry-ready.
- Which careers align with their current skills.
- Which skills they are missing.
- What a particular job actually feels like.
- How to become job-ready.

Traditional career platforms usually recommend careers using personality tests or keyword matching, but they rarely provide practical career exploration.

CareerVerse solves this through AI-powered simulations and personalized guidance.

---

# Objectives

The MVP should allow users to:

- Upload a resume.
- Upload multiple Job Description PDFs.
- Analyze resume quality.
- Retrieve relevant job descriptions using RAG.
- Recommend the Top 3 most suitable career paths.
- Allow users to explore recommended careers.
- Experience realistic AI-powered job simulations.
- Identify technical and soft skill gaps.
- Interact with an AI Career Mentor.
- Generate a personalized 3-month learning roadmap.

---

# Target Users

Primary Users

- University students
- Fresh graduates
- Internship seekers

Secondary Users

- Career switchers
- Early professionals

---

# User Journey

Landing

↓

Login / Signup

↓

Upload Resume

↓

Resume Parsing

↓

Resume Analysis

↓

Upload Job Description PDFs

↓

RAG Retrieval

↓

Top 3 Career Recommendations

↓

Career Match Explorer

↓

User selects one career

↓

Career Mentor Chatbot

↓

Interactive Job Simulation

↓

Simulation Evaluation

↓

Skill Gap Analysis

↓

Personalized Learning Roadmap

↓

Final Dashboard

---

# Core Features

## 1. Resume Analysis

The user uploads a PDF resume.

The Resume Reviewer Agent extracts:

- Skills
- Education
- Experience
- Projects
- Certifications

Outputs:

- Resume Score
- ATS Score
- Strengths
- Weaknesses
- Resume Suggestions

---

## 2. Job Description RAG

Users upload multiple Job Description PDFs.

The system:

- Extracts text
- Chunks documents
- Generates embeddings
- Stores embeddings inside ChromaDB
- Retrieves the most relevant job descriptions

The LLM should always answer using retrieved context.

---

## 3. Career Recommendation

Using

- Resume
- Retrieved Job Descriptions

The Career Recommendation Agent returns

Top 3 recommended careers.

Each recommendation includes:

- Match Percentage
- Why it matches
- Missing Skills
- Career Summary

---

## 4. Career Match Explorer

Users can explore every recommended career.

Each career card shows:

- Match %
- Career Overview
- Required Skills
- Missing Skills
- Expected Responsibilities

Every card contains

"Experience this Career"

---

## 5. AI Job Simulation

The Simulation Agent generates a realistic workplace scenario.

Example:

Software Engineer

- Production bug
- Code review
- Team discussion

Product Manager

- Stakeholder conflict
- Sprint planning

Data Scientist

- Dataset analysis
- Model selection

Simulation lasts approximately 5–10 conversational turns.

Outputs:

- Simulation Score
- Decision Feedback
- Communication Score
- Problem Solving Score

---

## 6. Skill Gap Analysis

Combines

- Resume Analysis
- Selected Career
- Simulation Performance

Outputs

Technical Skills Missing

Soft Skills Missing

Improvement Suggestions

---

## 7. Career Mentor Chatbot

A RAG-powered AI assistant.

Can answer questions like:

- Why was this career recommended?
- Which projects should I build?
- Which technologies should I learn?
- Compare Software Engineer vs Product Manager.
- Explain skills required for this role.
- Recommend learning resources.

The chatbot must only answer using retrieved knowledge and generated analysis.

---

## 8. Personalized Learning Roadmap

Generate a personalized

3-Month Learning Plan

Month 1

↓

Month 2

↓

Month 3

Each month contains

- Learning Goals
- Topics
- Resources
- Practice Suggestions

---

## 9. Dashboard

The final dashboard displays:

- Resume Score
- ATS Score
- Top 3 Career Matches
- Simulation Results
- Skill Gap Summary
- Learning Roadmap
- Career Mentor Access

---

# AI Agents

Resume Reviewer Agent

↓

Career Recommendation Agent

↓

Simulation Agent

↓

Skill Gap Agent

↓

Roadmap Agent

↓

Career Mentor Chatbot

Each agent has one responsibility and one dedicated prompt template.

---

# Non-Functional Requirements

- Responsive UI
- Modern SaaS Design
- Modular Architecture
- Reusable Components
- Explainable AI Outputs
- Fast Response Time
- Production-ready Code
- Clean Folder Structure

---

# MVP Scope

Included

✅ Resume Analysis

✅ RAG

✅ Top 3 Career Recommendations

✅ Career Match Explorer

✅ Job Simulation

✅ Skill Gap Analysis

✅ Career Mentor Chatbot

✅ Learning Roadmap

Excluded

❌ Voice Interviews

❌ Recruiter Portal

❌ Real Job APIs

❌ Multi-user Collaboration

❌ Resume Version History

---

# Success Criteria

A user should be able to:

1. Upload a resume.
2. Upload job descriptions.
3. Receive AI-generated career recommendations.
4. Explore recommended careers.
5. Complete a job simulation.
6. Understand skill gaps.
7. Receive a personalized roadmap.
8. Leave with a clear understanding of which career suits them best.