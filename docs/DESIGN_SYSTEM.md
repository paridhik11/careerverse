# CareerVerse Design System

> Visual language for CareerVerse AI — Emergent-inspired: warm cream canvas, white floating cards, soft violet edge glows, and a single purple accent.

---

## Design Principles

| Principle | Guidance |
|---|---|
| **Calm over flashy** | Warm cream background + soft violet edge glows. Hierarchy from spacing and type, not colored panels. |
| **Readability over decoration** | Fraunces for identity/titles, Manrope for information. Black headings, grey body. |
| **Soft rounded corners** | Cards ~30px (`--cv-radius-card`), large shells ~32px (`--cv-radius-main`), chips/buttons are full pills. |
| **White cards, thin borders** | Cards are white with a hairline neutral border and soft layered shadow — never pastel fills. |
| **One accent only** | Purple `#6B5CFF` (`--cv-accent`) is the sole primary accent (icons, badges, links, focus). |
| **Motion supports interaction** | Entrance 350–450ms expo-out. Glow blobs / mentor ring pause under `prefers-reduced-motion`. |
| **Consistent spacing** | Use the `--cv-space-*` scale (8px base). |

---

## Color Palette

All tokens live in `frontend/src/index.css` under `:root`.

### Layout & Structure

| Token | Value | Role |
|---|---|---|
| `--cv-bg` | `#FAF7F2` | Warm cream app canvas |
| `--cv-bg-elevated` / `--cv-card-surface` | `#FFFFFF` | Floating card / panel fill |
| `--cv-ink` | `#111827` | Headings |
| `--cv-ink-muted` | `#6B7280` | Body / secondary text |
| `--cv-accent` | `#6B5CFF` | Sole primary accent |
| `--cv-accent-muted` | `#6B5CFF1F` | Soft badge / pill fill |
| `--cv-accent-soft` | `#EEEBFF` | Purple icon circle fill |
| `--cv-border` | `rgba(17,24,39,0.08)` | Thin card border |
| `--cv-glow-*` | soft violet family | Blurred edge glow blobs |

### Legacy pastel aliases

`--cv-card-amber|sage|sky|lavender` all resolve to **white**.  
`--cv-card-*-icon` all resolve to **`--cv-accent-soft`**.  
Kept so older components keep compiling while the UI stays Emergent-white.

---

## Typography

| Token | Family | Use |
|---|---|---|
| `--cv-font-serif` | **Fraunces** | Headings, logo, card titles |
| `--cv-font-sans` | **Manrope** | Body, labels, badges, nav, buttons |

Type scale: `--cv-text-display` → `--cv-text-caption` (unchanged sizes).

---

## Radius & Elevation

| Token | Value |
|---|---|
| `--cv-radius-card` | `1.875rem` (30px) |
| `--cv-radius-main` | `2rem` (32px) |
| `--cv-radius-chip` | `9999px` |
| `--cv-shadow-card` | layered soft shadow |
| `--cv-shadow-main` | deeper layered shell shadow |

Utility classes: `.cv-card`, `.cv-icon-circle`, `.cv-badge`.

---

## Card anatomy

```
┌── white · border · radius 30px · soft shadow ─────────────────────┐
│  [purple icon ○]   Title (Fraunces)              [CATEGORY badge] │
│                    Description (Manrope grey)                      │
│                    [pill CTA]                                      │
└────────────────────────────────────────────────────────────────────┘
```

No yellow / green / blue / lavender card fills.

---

## Motion

Easing: `cubic-bezier(0.22, 1, 0.36, 1)`.

| Context | Notes |
|---|---|
| Section / card enter | opacity + y, ~400ms |
| Card hover | lift 2–6px + shadow deepen |
| Glow blobs / mentor ring | slow loops; off when `prefers-reduced-motion` |
