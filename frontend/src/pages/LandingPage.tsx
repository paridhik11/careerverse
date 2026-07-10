import { useReducedMotion, motion } from "framer-motion"
import {
  FileText,
  Briefcase,
  Sparkles,
  Users,
  Map,
  Upload,
  BrainCircuit,
  ArrowRight,
} from "lucide-react"
import { FeatureCard } from "@/components/FeatureCard"

/* ─── Animation helpers ──────────────────────────────────────────────────── */

const EASE = [0.22, 1, 0.36, 1] as const

/*
 * makeScroll builds whileInView animation props.
 * Call useReducedMotion() at the component top level, then pass the result
 * here — this keeps hook calls out of loops and satisfies the Rules of Hooks.
 */
function makeScroll(reduced: boolean | null, delay = 0) {
  if (reduced) return {}
  return {
    initial:     { opacity: 0, y: 16 },
    whileInView: { opacity: 1, y: 0 },
    viewport:    { once: true, margin: "-60px" },
    transition:  { duration: 0.4, delay, ease: EASE },
  }
}

/* ─── Feature card data ──────────────────────────────────────────────────── */

const features = [
  {
    title:        "Resume Review",
    description:  "Scores your resume against ATS criteria and surfaces specific improvements for your target role.",
    colorVariant: "amber"    as const,
    icon:         FileText,
  },
  {
    title:        "Career Match Explorer",
    description:  "Compares your resume against the job descriptions you upload and ranks your top 3 career fits by match percentage.",
    colorVariant: "sage"     as const,
    icon:         Briefcase,
  },
  {
    title:        "AI Job Simulation",
    description:  "Drops you into a realistic workplace scenario for your chosen career — 5–10 conversational turns of actual role experience.",
    colorVariant: "lavender" as const,
    icon:         Sparkles,
  },
  {
    title:        "Career Mentor",
    description:  "Answers your career questions using your own resume data, match analysis, and simulation results — grounded in your context only.",
    colorVariant: "lavender" as const,
    icon:         Users,
  },
  {
    title:        "Learning Roadmap",
    description:  "Builds a 3-month plan with weekly goals, curated resources, and practice tasks based on your specific skill gaps.",
    colorVariant: "sky"      as const,
    icon:         Map,
  },
]

/* ─── How It Works steps ─────────────────────────────────────────────────── */

const howItWorksSteps = [
  {
    icon:    Upload,
    label:   "Upload Resume",
    detail:  "Drop your PDF resume to start.",
  },
  {
    icon:    BrainCircuit,
    label:   "AI Analysis",
    detail:  "AI scores it and extracts your skills.",
  },
  {
    icon:    Briefcase,
    label:   "Top 3 Matches",
    detail:  "Ranked against your uploaded job descriptions.",
  },
  {
    icon:    Sparkles,
    label:   "Experience a Role",
    detail:  "Simulate a workday for your chosen career.",
  },
  {
    icon:    Map,
    label:   "Learning Roadmap",
    detail:  "Get a 3-month plan tailored to your gaps.",
  },
]

/* ─── Navbar ─────────────────────────────────────────────────────────────── */

function Navbar() {
  return (
    <header
      className="sticky top-0 z-50 w-full border-b border-black/5"
      style={{ background: "rgba(237, 234, 227, 0.92)", backdropFilter: "blur(12px)" }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <a
          href="#"
          className="flex items-baseline gap-1 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          aria-label="CareerVerse home"
        >
          <span
            className="text-gray-900"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize:   "1.25rem",
              fontWeight: 500,
            }}
          >
            CareerVerse
          </span>
          <span
            className="text-xs font-semibold tracking-widest"
            style={{ color: "var(--cv-accent)", fontFamily: "var(--cv-font-sans)" }}
          >
            AI
          </span>
        </a>

        {/* Nav links */}
        <nav className="hidden items-center gap-8 sm:flex" aria-label="Main navigation">
          {[
            { label: "Features",     href: "#features"     },
            { label: "How It Works", href: "#how-it-works" },
          ].map(({ label, href }) => (
            <a
              key={label}
              href={href}
              className="text-gray-600 transition-colors duration-150 hover:text-gray-900 focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
              style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", fontWeight: 500 }}
            >
              {label}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <a
          href="/signup"
          className="rounded-full px-5 py-2.5 font-semibold text-white transition-opacity duration-150 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          style={{
            background:  "var(--cv-accent)",
            fontFamily:  "var(--cv-font-sans)",
            fontSize:    "var(--cv-text-small)",
          }}
        >
          Start Exploring
        </a>
      </div>
    </header>
  )
}

/* ─── Hero section ───────────────────────────────────────────────────────── */

function HeroSection() {
  const reduced = useReducedMotion()

  const headlineProps = reduced ? {} : {
    initial:    { opacity: 0, y: 20 },
    animate:    { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: EASE },
  }

  const subheadProps = reduced ? {} : {
    initial:    { opacity: 0, y: 16 },
    animate:    { opacity: 1, y: 0 },
    transition: { duration: 0.4, delay: 0.1, ease: EASE },
  }

  const ctaProps = reduced ? {} : {
    initial:    { opacity: 0, y: 12 },
    animate:    { opacity: 1, y: 0 },
    transition: { duration: 0.4, delay: 0.2, ease: EASE },
  }

  return (
    <section
      className="flex min-h-[90svh] flex-col items-center justify-center px-6 py-24 text-center"
      aria-labelledby="hero-headline"
    >
      <motion.h1
        id="hero-headline"
        className="mx-auto max-w-4xl text-gray-900"
        style={{
          fontFamily:  "var(--cv-font-serif)",
          fontSize:    "var(--cv-text-display)",
          fontWeight:  300,
          lineHeight:  1.1,
          letterSpacing: "-0.01em",
        }}
        {...headlineProps}
      >
        Discover. Experience.{" "}
        <br className="hidden sm:block" />
        Build Your Career.
      </motion.h1>

      <motion.p
        className="mx-auto mt-6 max-w-xl text-gray-600"
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize:   "var(--cv-text-body)",
          lineHeight: 1.7,
        }}
        {...subheadProps}
      >
        CareerVerse analyzes your resume, matches it against the job descriptions
        you upload, and recommends the top 3 careers that fit your skills. Pick one,
        simulate a real workday in that role, and get a personalized roadmap to close
        your skill gaps.
      </motion.p>

      <motion.div
        className="mt-10 flex flex-wrap items-center justify-center gap-4"
        {...ctaProps}
      >
        {/* Primary CTA */}
        <a
          href="/signup"
          className="flex items-center gap-2 rounded-full px-7 py-3.5 font-semibold text-white transition-opacity duration-150 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          style={{
            background:  "var(--cv-accent)",
            fontFamily:  "var(--cv-font-sans)",
            fontSize:    "var(--cv-text-body)",
          }}
        >
          Start Exploring
          <ArrowRight className="h-4 w-4" strokeWidth={2} />
        </a>

        {/*
         * TODO: Replace this anchor with a modal or video player trigger once
         * a demo video is available. Currently smooth-scrolls to the How It Works
         * section as a functional fallback.
         */}
        <a
          href="#how-it-works"
          className="flex items-center gap-2 rounded-full border border-gray-300 px-7 py-3.5 font-semibold text-gray-700 transition-colors duration-150 hover:border-gray-400 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          style={{
            fontFamily:  "var(--cv-font-sans)",
            fontSize:    "var(--cv-text-body)",
            background:  "transparent",
          }}
        >
          Watch Demo
        </a>
      </motion.div>
    </section>
  )
}

/* ─── Features section ───────────────────────────────────────────────────── */

/*
 * Layout decision: 3-up top row + 2-up bottom row (centered)
 *
 * Why not 5 equal columns: At reasonable viewport widths each card becomes too
 * narrow to breathe. Five equal columns also imply equal visual weight, which
 * loses natural reading hierarchy.
 *
 * Why 3+2 over 2+3: The three primary features (Resume Review, Career Match,
 * AI Simulation) are the core pipeline. Placing them on top communicates
 * importance. Career Mentor and Learning Roadmap are supporting/downstream
 * features — a two-card row below naturally reads as "and then you also get."
 *
 * On tablet (< 1024px): two columns. On mobile (< 640px): single column.
 */
function FeaturesSection() {
  const reduced   = useReducedMotion()
  const topRow    = features.slice(0, 3)
  const bottomRow = features.slice(3)

  return (
    <section
      id="features"
      className="mx-auto w-full max-w-6xl px-6 py-24"
      aria-labelledby="features-heading"
    >
      {/* Section header */}
      <motion.div className="mb-14 text-center" {...makeScroll(reduced)}>
        <h2
          id="features-heading"
          className="text-gray-900"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize:   "var(--cv-text-h1)",
            fontWeight: 400,
            lineHeight: 1.15,
          }}
        >
          Everything you need to choose confidently
        </h2>
        <p
          className="mx-auto mt-3 max-w-lg text-gray-500"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize:   "var(--cv-text-body)",
            lineHeight: 1.6,
          }}
        >
          Five tools that take you from a raw resume to a clear career decision — and a plan to get there.
        </p>
      </motion.div>

      {/* 3-up top row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {topRow.map((card, i) => (
          <motion.div key={card.title} {...makeScroll(reduced, i * 0.07)}>
            <FeatureCard {...card} className="h-full" />
          </motion.div>
        ))}
      </div>

      {/* 2-up bottom row — centered on large screens */}
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:mx-auto lg:max-w-[calc(66.666%+0.5rem)]">
        {bottomRow.map((card, i) => (
          <motion.div key={card.title} {...makeScroll(reduced, (topRow.length + i) * 0.07)}>
            <FeatureCard {...card} className="h-full" />
          </motion.div>
        ))}
      </div>
    </section>
  )
}

/* ─── How It Works section ───────────────────────────────────────────────── */

function HowItWorksSection() {
  const reduced = useReducedMotion()

  return (
    <section
      id="how-it-works"
      className="w-full py-24"
      style={{ background: "var(--cv-sidebar)" }}
      aria-labelledby="hiw-heading"
    >
      <div className="mx-auto max-w-6xl px-6">
        {/* Section header */}
        <motion.div className="mb-16 text-center" {...makeScroll(reduced)}>
          <h2
            id="hiw-heading"
            className="text-white"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize:   "var(--cv-text-h1)",
              fontWeight: 400,
              lineHeight: 1.15,
            }}
          >
            How it works
          </h2>
          <p
            className="mx-auto mt-3 max-w-md"
            style={{
              color:      "var(--cv-sidebar-text)",
              fontFamily: "var(--cv-font-sans)",
              fontSize:   "var(--cv-text-body)",
              lineHeight: 1.6,
            }}
          >
            Five steps from resume upload to a personalized roadmap. The whole flow takes under 20 minutes.
          </p>
        </motion.div>

        {/* Timeline */}
        <ol className="flex flex-col items-start gap-8 lg:flex-row lg:items-start lg:gap-0">
          {howItWorksSteps.map((step, i) => {
            const isLast = i === howItWorksSteps.length - 1

            return (
              <motion.li
                key={step.label}
                className="flex flex-1 flex-row items-start gap-4 lg:flex-col lg:items-center lg:text-center"
                {...makeScroll(reduced, i * 0.08)}
              >
                {/* Step + connector row */}
                <div className="flex flex-col items-center lg:w-full lg:flex-row">
                  {/* Circle */}
                  <div
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
                    style={{ background: "var(--cv-accent-muted)", border: "1.5px solid var(--cv-accent)" }}
                    aria-hidden="true"
                  >
                    <step.icon
                      className="h-5 w-5"
                      style={{ color: "var(--cv-accent)" }}
                      strokeWidth={1.8}
                    />
                  </div>

                  {/* Connector line — hidden on last item */}
                  {!isLast && (
                    <div
                      className="hidden w-full border-t border-dashed lg:block"
                      style={{ borderColor: "rgba(107, 127, 255, 0.3)" }}
                      aria-hidden="true"
                    />
                  )}

                  {/* Vertical connector for mobile */}
                  {!isLast && (
                    <div
                      className="ml-[23px] mt-2 h-8 border-l border-dashed lg:hidden"
                      style={{ borderColor: "rgba(107, 127, 255, 0.3)" }}
                      aria-hidden="true"
                    />
                  )}
                </div>

                {/* Text */}
                <div className="flex flex-col gap-1 pb-2 lg:mt-4 lg:items-center lg:px-2">
                  {/* Step number badge */}
                  <span
                    className="mb-1 w-fit rounded-full px-2.5 py-0.5 text-center"
                    style={{
                      background:  "var(--cv-accent-muted)",
                      color:       "var(--cv-accent)",
                      fontFamily:  "var(--cv-font-sans)",
                      fontSize:    "var(--cv-text-caption)",
                      fontWeight:  600,
                    }}
                  >
                    Step {i + 1}
                  </span>
                  <span
                    className="text-white"
                    style={{
                      fontFamily: "var(--cv-font-serif)",
                      fontSize:   "var(--cv-text-h3)",
                      fontWeight: 500,
                      lineHeight: 1.3,
                    }}
                  >
                    {step.label}
                  </span>
                  <span
                    style={{
                      color:       "var(--cv-sidebar-text)",
                      fontFamily:  "var(--cv-font-sans)",
                      fontSize:    "var(--cv-text-small)",
                      lineHeight:  1.5,
                    }}
                  >
                    {step.detail}
                  </span>
                </div>
              </motion.li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}

/* ─── Footer ─────────────────────────────────────────────────────────────── */

function Footer() {
  return (
    <footer
      className="w-full border-t border-white/10 px-6 py-12"
      style={{ background: "var(--cv-sidebar)" }}
      aria-label="Site footer"
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-8 sm:flex-row sm:items-start sm:justify-between">
        {/* Brand */}
        <div className="flex flex-col items-center gap-2 sm:items-start">
          <div className="flex items-baseline gap-1">
            <span
              className="text-white"
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize:   "1.25rem",
                fontWeight: 500,
              }}
            >
              CareerVerse
            </span>
            <span
              className="text-xs font-semibold tracking-widest"
              style={{ color: "var(--cv-accent)", fontFamily: "var(--cv-font-sans)" }}
            >
              AI
            </span>
          </div>
          <p
            style={{
              color:      "var(--cv-sidebar-text)",
              fontFamily: "var(--cv-font-sans)",
              fontSize:   "var(--cv-text-small)",
              lineHeight: 1.5,
            }}
          >
            Experience the role before choosing your future.
          </p>
        </div>

        {/* Links */}
        <nav aria-label="Footer navigation">
          <ul className="flex flex-wrap justify-center gap-6 sm:justify-end">
            {[
              { label: "Features",     href: "#features"     },
              { label: "How It Works", href: "#how-it-works" },
              { label: "Sign Up",      href: "/signup"       },
            ].map(({ label, href }) => (
              <li key={label}>
                <a
                  href={href}
                  className="transition-colors duration-150 hover:text-white focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
                  style={{
                    color:      "var(--cv-sidebar-text)",
                    fontFamily: "var(--cv-font-sans)",
                    fontSize:   "var(--cv-text-small)",
                    fontWeight: 500,
                  }}
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Copyright */}
      <div className="mx-auto mt-10 max-w-6xl border-t border-white/10 pt-6 text-center">
        <p
          style={{
            color:      "var(--cv-sidebar-text)",
            fontFamily: "var(--cv-font-sans)",
            fontSize:   "var(--cv-text-caption)",
          }}
        >
          © {new Date().getFullYear()} CareerVerse AI. MVP build — not yet in production.
        </p>
      </div>
    </footer>
  )
}

/* ─── Page ───────────────────────────────────────────────────────────────── */

export function LandingPage() {
  return (
    <div
      className="min-h-screen w-full"
      style={{ background: "var(--cv-bg)" }}
    >
      <Navbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
      </main>
      <Footer />
    </div>
  )
}
