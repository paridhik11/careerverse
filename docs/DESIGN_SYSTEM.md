# CareerVerse Design System

> Visual language for CareerVerse AI — a career exploration platform that feels calm, intelligent, and human.
> Inspired by floating card-based dashboards with pastel surfaces, expressive typography, and purposeful motion.

---

## Design Principles

| Principle | Guidance |
|---|---|
| **Calm over flashy** | No gradients for decoration, no bright backgrounds. Let soft pastels and white space breathe. |
| **Readability over decoration** | Type is the primary UI element. Fraunces for identity/titles, Manrope for information. |
| **Soft rounded corners** | Every surface uses generous border-radius. Cards at 20px, the main shell at 24px, chips are full pills. |
| **Pastel surfaces instead of harsh borders** | Card identity comes from background color, not outlines. Avoid 1px borders as dividers — use spacing. |
| **Motion should support interaction, never distract** | Entrance animations are 350–400ms, eased with `[0.22, 1, 0.36, 1]` (expo-out feel). Hover states are 150–200ms transitions. No looping or ambient animations. |
| **One accent color per feature** | Each feature maps to exactly one pastel + one chip color. Never mix card palettes. |
| **Consistent spacing and typography throughout** | Use the `--cv-space-*` scale (8px base). Type size choices come from the token scale only. |

---

## Color Palette

All tokens are defined as CSS custom properties in `frontend/src/index.css` under `:root`.

### Layout & Structure

| Token | Value | Role |
|---|---|---|
| `--cv-sidebar` | `#1E2028` | Dark charcoal sidebar background |
| `--cv-sidebar-text` | `#C8CAD4` | Muted nav labels (inactive) |
| `--cv-sidebar-active` | `#FFFFFF` | Active nav label |
| `--cv-bg` | `#EDEAE3` | Warm off-white app canvas |
| `--cv-accent` | `#6B7FFF` | Indigo — active nav, chips, links |
| `--cv-accent-muted` | `#6B7FFF26` | Accent at ~15% opacity (active nav pill bg) |

### Pastel Card Surfaces

Each feature owns a pastel background and a slightly deeper icon circle shade.

| Feature | Card bg token | Value | Icon bg token | Value |
|---|---|---|---|---|
| Resume Review | `--cv-card-amber` | `#FEF2BF` | `--cv-card-amber-icon` | `#F6DC6D` |
| Job Match | `--cv-card-sage` | `#D4EDD8` | `--cv-card-sage-icon` | `#9DD4A8` |
| Skill Gap Analysis | `--cv-card-sky` | `#D5E8F8` | `--cv-card-sky-icon` | `#93C6ED` |
| AI Simulation | `--cv-card-lavender` | `#E7DDF8` | `--cv-card-lavender-icon` | `#C5A8EF` |
| Career Mentor | `--cv-card-lavender` | `#E7DDF8` | `--cv-card-lavender-icon` | `#C5A8EF` |

### Status Chip Colors

| Status | Dot color | Background | Text |
|---|---|---|---|
| Ready | `#6B7FFF` | accent at 15% | `#4A5FD4` |
| In Progress | `#F59E0B` | amber-100 | amber-700 |
| Locked | `#9CA3AF` | gray-100 | gray-500 |

---

## Typography

### Font Families

| Token | Family | Fallback | Use |
|---|---|---|---|
| `--cv-font-serif` | **Fraunces** | Georgia, serif | All headings, card titles, logo, page titles |
| `--cv-font-sans` | **Manrope** | system-ui, sans-serif | All body copy, labels, chips, nav, inputs |

Loaded via Google Fonts (variable fonts for Fraunces, static for Manrope):
```
https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..500&family=Manrope:wght@400;500;600;700&display=swap
```

### Type Scale

| Token | Size | Family | Weight | Line-height | Use |
|---|---|---|---|---|---|
| `--cv-text-display` | `clamp(2.5rem, 5vw, 3rem)` | Fraunces | 300 | 1.1 | Hero/marketing headlines |
| `--cv-text-h1` | `2.25rem` (36px) | Fraunces | 400 | 1.15 | Page titles |
| `--cv-text-h2` | `1.75rem` (28px) | Fraunces | 400 | 1.2 | Section headings, top bar title |
| `--cv-text-h3` | `1.25rem` (20px) | Fraunces | 500 | 1.3 | Journey card titles |
| `--cv-text-body` | `1rem` (16px) | Manrope | 400 | 1.6 | Paragraphs, descriptions |
| `--cv-text-small` | `0.875rem` (14px) | Manrope | 500 | 1.5 | Card descriptions, nav labels |
| `--cv-text-caption` | `0.75rem` (12px) | Manrope | 400–500 | 1.4 | Chips, timestamps, metadata |

---

## Spacing

8px base grid. Use the `--cv-space-*` tokens or Tailwind's default scale (which is also 4px-based).

| Token | Value | Equivalent |
|---|---|---|
| `--cv-space-1` | `0.5rem` | 8px |
| `--cv-space-2` | `1rem` | 16px |
| `--cv-space-3` | `1.5rem` | 24px |
| `--cv-space-4` | `2rem` | 32px |
| `--cv-space-6` | `3rem` | 48px |

---

## Border Radius

| Token | Value | Use |
|---|---|---|
| `--cv-radius-card` | `1.25rem` (20px) | Journey cards |
| `--cv-radius-main` | `1.5rem` (24px) | Main content shell |
| `--cv-radius-chip` | `9999px` | Status chips, date chip, search pill |

---

## Elevation / Shadows

| Token | Value | Use |
|---|---|---|
| `--cv-shadow-card` | `0 2px 8px 0 rgb(0 0 0 / 0.06)` | Default card shadow |
| `--cv-shadow-main` | `0 8px 32px 0 rgb(0 0 0 / 0.10)` | Main floating content shell |
| Hover state | `0 4px 16px 0 rgb(0 0 0 / 0.10)` | Card on `:hover` (transition 200ms) |

---

## Lucide Icon Mapping

All icons use `lucide-react`. Standard stroke width: `1.6` (inactive), `2` (active/emphasized).

| Feature | Icon | Lucide name |
|---|---|---|
| Dashboard / Overview | `LayoutDashboard` | `layout-dashboard` |
| Resume Review | `FileText` | `file-text` |
| Job Match | `Briefcase` | `briefcase` |
| Skill Gap Analysis | `BarChart2` | `bar-chart-2` |
| AI Simulation | `Sparkles` | `sparkles` |
| Career Mentor | `Users` | `users` |
| Interview Prep | `BookOpen` | `book-open` |
| Chat / Messages | `MessageSquare` | `message-square` |
| Search | `Search` | `search` |
| Notifications | `Bell` | `bell` |
| Settings | `Settings` | `settings` |
| Upload (Resume) | `Upload` | `upload` |
| Roadmap / Progress | `Map` | `map` |
| Locked content | `Lock` | `lock` |

---

## Layout Architecture

```
App shell — bg: --cv-bg, full viewport
├── Sidebar (fixed 220px)
│   ├── Logo (Fraunces serif + "AI" accent label)
│   └── Nav items (icon + label, active = indigo pill)
└── Main card (flex-1, margin: 12px, rounded-[24px], bg: white, shadow: --cv-shadow-main)
    ├── Top bar (date chip · page title · search input)
    └── Content area (scrollable, px-8 py-8)
        └── Journey cards (stacked column, gap-4)
```

### Journey Card anatomy

```
┌── rounded-[20px], pastel bg, p-5, shadow-card ──────────────────┐
│  [icon circle]   Title (Fraunces 20px 500)      [● Status chip]  │
│  (44px circle,   Description (Manrope 14px,                      │
│   deeper pastel)  text-gray-600, 1.5 line-height)                │
└─────────────────────────────────────────────────────────────────┘
```

**Props:** `title`, `description`, `colorVariant` (`amber | sage | sky | lavender`), `icon` (LucideIcon), `statusLabel` (string), `statusVariant` (`ready | progress | locked`)

---

## Motion

All entrance animations share the same easing curve: `cubic-bezier(0.22, 1, 0.36, 1)` (expo-out).

| Context | Duration | Style |
|---|---|---|
| Page / section entrance | 400ms | `opacity: 0→1, y: 8→0` |
| Journey card entrance | 350ms + stagger 70ms/card | `opacity: 0→1, y: 12→0` |
| Card hover shadow | 200ms | CSS `transition-shadow` |
| Nav item state change | 150ms | CSS `transition-colors` |

No looping, no ambient, no parallax. Motion is always in response to a user action or page load.

---

## Component Index

| Component | Path | Status |
|---|---|---|
| `JourneyCard` | `src/components/JourneyCard.tsx` | ✅ Built |
| `Sidebar` | `src/App.tsx` → extracted next | ⬜ Inline (extract when page routing added) |
| `TopBar` | `src/App.tsx` → extracted next | ⬜ Inline |
| `StatusChip` | inside `JourneyCard.tsx` | ⬜ Extract if used standalone |
