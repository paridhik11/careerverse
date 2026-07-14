# CareerVerse AI :AI Powered Career Guidance and Resume Analysis Platform

CareerVerse AI is an AI-powered web application designed to help students make better career decisions by combining resume analysis, job compatibility, career exploration, and realistic work simulations into one platform.
Instead of only checking whether a resume looks "good", CareerVerse AI helps users understand **which careers suit their current profile, why they match those careers, what skills they still need, and what working in those roles actually feels like.**


# Problem Statement

Every year, thousands of students apply for internships and placements without fully understanding the roles they are applying for.

Many students face challenges such as:

* Creating resumes without knowing whether they match industry expectations.
* Applying to job roles simply because they sound interesting, without understanding the actual work involved.
* Being confused by different job titles such as Software Engineer, Backend Engineer, Machine Learning Engineer, Platform Engineer, DevOps Engineer, Data Engineer, and many more.
* Receiving generic career advice that is not based on their own resume or skills.
* Not knowing which skills they should learn next to become eligible for their target career.

A resume score alone cannot answer these questions.

Similarly, reading a job description rarely helps students understand what the job actually looks like in practice.

CareerVerse AI was built to bridge this gap by helping students explore careers in a practical, interactive, and personalized way before they begin preparing for them.

---

# Our Solution

CareerVerse AI combines multiple AI-powered modules that can be used independently after uploading a resume.

Instead of forcing users through one fixed pipeline, every module answers a different question.

### Resume Analysis

Answers:

> "How strong is my resume?"

The resume is parsed and reviewed using AI to generate:

* Resume score
* Strengths
* Weaknesses
* Suggestions for improvement

---

### Career Compatibility

Answers:

> "How well does my resume match this specific job?"

The user can:

* Upload their own Job Description
* Select one of the provided sample job descriptions

CareerVerse AI compares the resume against the selected role and provides:

* Compatibility percentage
* Matching skills
* Missing skills
* Areas that require improvement

---

### Career Explorer

Answers:

> "Which careers am I currently best suited for?"

Rather than evaluating only one selected job description, Career Explorer analyzes the resume as a whole and identifies the user's Top 3 career matches.

Each recommendation includes:

* Match percentage
* Confidence level
* Reasoning behind the recommendation

This allows users to discover career paths they may not have considered before.

---

### Virtual Experience

Understanding a job title is very different from understanding the work done in that role.

For every recommended career, CareerVerse AI generates an interactive workplace simulation based on real job responsibilities.

Instead of reading bullet points from a job description, users experience:

* Daily responsibilities
* Workplace decisions
* Practical scenarios
* Realistic tasks

This helps students understand whether they would actually enjoy working in that role before spending months preparing for it.

---

### Skill Gap Analysis

Once the user selects a career, CareerVerse AI compares:

Resume

↓

Chosen Career

↓

Required Skills

It identifies:

* Missing technical skills
* Missing tools
* Knowledge gaps
* Recommended improvements

---

### Learning Roadmap

Based on the identified skill gaps, CareerVerse AI creates a personalized three-month learning roadmap.

Instead of recommending random online courses, the roadmap focuses on preparing the user for the specific career they selected.

---

### Career Mentor

A floating AI mentor remains available throughout the application.

Users can ask career-related questions at any stage, including:

* Resume advice
* Career guidance
* Skill recommendations
* Technology suggestions
* Placement preparation

---

# User Flow

```text
Upload Resume
      │
      ├────────► Resume Analysis
      │
      ├────────► Career Compatibility
      │
      └────────► Career Explorer
                    │
                    ▼
            Virtual Experience
                    │
             Choose This Career
                    │
                    ▼
      Skill Gap Analysis + Learning Roadmap
```

The first three modules are completely independent.

Users can explore any of them immediately after uploading their resume.

Virtual Experience becomes available after Career Explorer recommends suitable careers.

Once a career is selected, Skill Gap Analysis and the personalized Learning Roadmap are unlocked.

---

# Features

* AI Resume Analysis
* Resume Scoring
* Career Compatibility Checker
* Career Explorer
* AI Career Recommendations
* Virtual Job Simulations
* Skill Gap Analysis
* Personalized Learning Roadmap
* Career Mentor Chatbot
* Resume-based Career Guidance

---

# Technology Stack

| Component       | Technology                      |
| --------------- | ------------------------------- |
| Frontend        | React, TypeScript, Tailwind CSS |
| Backend         | FastAPI                         |
| Database        | PostgreSQL                      |
| Vector Database | ChromaDB                        |
| AI Models       | OpenRouter LLMs                 |
| Embeddings      | Gemini Embeddings               |
| Authentication  | JWT                             |
| PDF Parsing     | PyMuPDF                         |

---
