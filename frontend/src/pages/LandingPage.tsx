/**
 * LandingPage — public marketing surface for CareerVerse AI.
 *
 * Motion: staggered hero fade-in, floating violet glow blobs, animated CTAs,
 * scroll-triggered feature cards with hover lift, smooth section reveals.
 * All ambient / entrance motion respects prefers-reduced-motion.
 */

import { useReducedMotion, motion, type Variants } from "framer-motion"
import type { ReactNode } from "react"
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

/* ─── Animation tokens ───────────────────────────────────────────────────── */

const EASE = [0.22, 1, 0.36, 1] as const

function makeScroll(reduced: boolean | null, delay = 0) {
  if (reduced) return {}
  return {
    initial: { opacity: 0, y: 20 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, margin: "-80px" },
    transition: { duration: 0.45, delay, ease: EASE },
  }
}

const heroStagger: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12, delayChildren: 0.06 },
  },
}

const heroItem: Variants = {
  hidden: { opacity: 0, y: 22 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: EASE },
  },
}

/* ─── Feature card data ──────────────────────────────────────────────────── */

const features = [
  {
    title: "Resume Review",
    description:
      "Scores your resume against ATS criteria and surfaces specific improvements for your target role.",
    colorVariant: "amber" as const,
    icon: FileText,
  },
  {
    title: "Career Match Explorer",
    description:
      "Compares your resume against the job descriptions you upload and ranks your top 3 career fits by match percentage.",
    colorVariant: "sage" as const,
    icon: Briefcase,
  },
  {
    title: "AI Job Simulation",
    description:
      "Drops you into a realistic workplace scenario for your chosen career — 5–10 conversational turns of actual role experience.",
    colorVariant: "lavender" as const,
    icon: Sparkles,
  },
  {
    title: "Career Mentor",
    description:
      "Answers your career questions using your own resume data, match analysis, and simulation results — grounded in your context only.",
    colorVariant: "lavender" as const,
    icon: Users,
  },
  {
    title: "Learning Roadmap",
    description:
      "Builds a 3-month plan with weekly goals, curated resources, and practice tasks based on your specific skill gaps.",
    colorVariant: "sky" as const,
    icon: Map,
  },
]

const howItWorksSteps = [
  {
    icon: Upload,
    label: "Upload Resume",
    detail: "Drop your PDF resume to start.",
  },
  {
    icon: BrainCircuit,
    label: "AI Analysis",
    detail: "AI scores it and extracts your skills.",
  },
  {
    icon: Briefcase,
    label: "Top 3 Matches",
    detail: "Ranked against your uploaded job descriptions.",
  },
  {
    icon: Sparkles,
    label: "Experience a Role",
    detail: "Simulate a workday for your chosen career.",
  },
  {
    icon: Map,
    label: "Learning Roadmap",
    detail: "Get a 3-month plan tailored to your gaps.",
  },
]

/* ─── Glow blobs ─────────────────────────────────────────────────────────── */

function GlowBlobs({ reduced }: { reduced: boolean | null }) {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div
        className="cv-glow-blob cv-glow-blob--a -left-28 -top-20 size-[26rem] md:size-[32rem]"
        style={reduced ? { animation: "none" } : undefined}
      />
      <div
        className="cv-glow-blob cv-glow-blob--b -right-24 top-[20%] size-[22rem] md:size-[28rem]"
        style={reduced ? { animation: "none" } : undefined}
      />
      <div
        className="cv-glow-blob cv-glow-blob--c bottom-[-10%] left-[35%] size-[18rem] md:size-[24rem]"
        style={reduced ? { animation: "none", opacity: 0.28 } : undefined}
      />
    </div>
  )
}

/* ─── Animated CTA ───────────────────────────────────────────────────────── */

function MotionCta({
  href,
  children,
  variant = "primary",
  reduced,
}: {
  href: string
  children: ReactNode
  variant?: "primary" | "secondary"
  reduced: boolean | null
}) {
  const isPrimary = variant === "primary"

  return (
    <motion.a
      href={href}
      className="inline-flex items-center gap-2 rounded-full px-7 py-3.5 font-semibold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
      style={{
        background: isPrimary ? "var(--cv-ink)" : "rgba(255,255,255,0.72)",
        color: isPrimary ? "#FFFFFF" : "var(--cv-ink)",
        border: isPrimary ? "none" : "1px solid rgba(17,24,39,0.14)",
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-body)",
        boxShadow: isPrimary ? "var(--cv-shadow-card)" : undefined,
      }}
      whileHover={
        reduced
          ? undefined
          : { y: -2, scale: 1.02, transition: { duration: 0.18, ease: EASE } }
      }
      whileTap={reduced ? undefined : { scale: 0.98 }}
    >
      {children}
    </motion.a>
  )
}

/* ─── Navbar ─────────────────────────────────────────────────────────────── */

function Navbar() {
  return (
    <header
      className="sticky top-0 z-50 w-full border-b border-black/[0.05]"
      style={{
        background: "rgba(250, 250, 252, 0.85)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a
          href="/"
          className="flex items-baseline gap-1.5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          aria-label="CareerVerse home"
        >
          <span
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "1.25rem",
              fontWeight: 500,
              color: "var(--cv-ink)",
              letterSpacing: "-0.02em",
            }}
          >
            CareerVerse
          </span>
          <span
            className="rounded-full px-2 py-0.5 text-xs font-bold tracking-widest"
            style={{
              color: "var(--cv-accent)",
              background: "var(--cv-accent-muted)",
              fontFamily: "var(--cv-font-sans)",
            }}
          >
            AI
          </span>
        </a>

        <nav className="hidden items-center gap-8 sm:flex" aria-label="Main navigation">
          {[
            { label: "Features", href: "#features" },
            { label: "How It Works", href: "#how-it-works" },
          ].map(({ label, href }) => (
            <a
              key={label}
              href={href}
              className="transition-colors duration-150 hover:text-[var(--cv-ink)] focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-small)",
                fontWeight: 500,
                color: "var(--cv-ink-muted)",
              }}
            >
              {label}
            </a>
          ))}
        </nav>

        <a
          href="/signup"
          className="rounded-full px-5 py-2.5 font-semibold text-white transition-opacity duration-150 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          style={{
            background: "var(--cv-ink)",
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
          }}
        >
          Start Exploring
        </a>
      </div>
    </header>
  )
}

/* ─── Hero ───────────────────────────────────────────────────────────────── */

function HeroSection() {
  const reduced = useReducedMotion()

  return (
    <section
      className="relative isolate flex min-h-[90svh] flex-col items-center justify-center overflow-hidden px-6 py-24 text-center"
      aria-labelledby="hero-headline"
    >
      <GlowBlobs reduced={reduced} />

      <motion.div
        className="relative z-[1] mx-auto flex max-w-4xl flex-col items-center"
        variants={reduced ? undefined : heroStagger}
        initial={reduced ? undefined : "hidden"}
        animate={reduced ? undefined : "visible"}
      >
        <motion.p
          variants={reduced ? undefined : heroItem}
          className="mb-5"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "clamp(1.75rem, 4vw, 2.25rem)",
            fontWeight: 500,
            color: "var(--cv-ink)",
            letterSpacing: "-0.02em",
            lineHeight: 1.15,
          }}
        >
          CareerVerse
          <span
            className="ml-2 align-middle text-xs font-bold tracking-widest"
            style={{
              fontFamily: "var(--cv-font-sans)",
              color: "var(--cv-accent)",
              background: "var(--cv-accent-muted)",
              borderRadius: 9999,
              padding: "0.2rem 0.55rem",
            }}
          >
            AI
          </span>
        </motion.p>

        <motion.h1
          id="hero-headline"
          variants={reduced ? undefined : heroItem}
          className="max-w-4xl"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-display)",
            fontWeight: 400,
            lineHeight: 1.08,
            letterSpacing: "-0.02em",
            color: "var(--cv-ink)",
          }}
        >
          Discover. Experience.
          <br className="hidden sm:block" />
          Build Your Career.
        </motion.h1>

        <motion.p
          variants={reduced ? undefined : heroItem}
          className="mx-auto mt-6 max-w-xl"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            lineHeight: 1.7,
            color: "var(--cv-ink-muted)",
          }}
        >
          CareerVerse analyzes your resume, matches it against the job descriptions
          you upload, and recommends the top 3 careers that fit your skills. Pick one,
          simulate a real workday in that role, and get a personalized roadmap to close
          your skill gaps.
        </motion.p>

        <motion.div
          variants={reduced ? undefined : heroItem}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <MotionCta href="/signup" reduced={reduced}>
            Start Exploring
            <ArrowRight className="h-4 w-4" strokeWidth={2} />
          </MotionCta>
          <MotionCta href="#how-it-works" variant="secondary" reduced={reduced}>
            How it works
          </MotionCta>
        </motion.div>
      </motion.div>
    </section>
  )
}

/* ─── Features ───────────────────────────────────────────────────────────── */

function FeaturesSection() {
  const reduced = useReducedMotion()
  const topRow = features.slice(0, 3)
  const bottomRow = features.slice(3)

  return (
    <motion.section
      id="features"
      className="relative mx-auto w-full max-w-6xl px-6 py-24"
      aria-labelledby="features-heading"
      {...makeScroll(reduced)}
    >
      <motion.div className="mb-14 text-center" {...makeScroll(reduced)}>
        <h2
          id="features-heading"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            lineHeight: 1.15,
            color: "var(--cv-ink)",
          }}
        >
          Everything you need to choose confidently
        </h2>
        <p
          className="mx-auto mt-3 max-w-lg"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            lineHeight: 1.6,
            color: "var(--cv-ink-muted)",
          }}
        >
          Five tools that take you from a raw resume to a clear career decision — and a
          plan to get there.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {topRow.map((card, i) => (
          <motion.div
            key={card.title}
            {...makeScroll(reduced, i * 0.08)}
            whileHover={
              reduced
                ? undefined
                : { y: -6, transition: { duration: 0.2, ease: EASE } }
            }
            style={{ willChange: "transform" }}
          >
            <FeatureCard {...card} className="h-full" />
          </motion.div>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:mx-auto lg:max-w-[calc(66.666%+0.5rem)]">
        {bottomRow.map((card, i) => (
          <motion.div
            key={card.title}
            {...makeScroll(reduced, (topRow.length + i) * 0.08)}
            whileHover={
              reduced
                ? undefined
                : { y: -6, transition: { duration: 0.2, ease: EASE } }
            }
            style={{ willChange: "transform" }}
          >
            <FeatureCard {...card} className="h-full" />
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}

/* ─── How It Works ───────────────────────────────────────────────────────── */

function HowItWorksSection() {
  const reduced = useReducedMotion()

  return (
    <section
      id="how-it-works"
      className="relative w-full overflow-hidden py-24"
      aria-labelledby="hiw-heading"
    >
      {/* Soft section wash + edge glows */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, transparent 0%, rgba(237,228,255,0.35) 50%, transparent 100%)",
        }}
        aria-hidden
      />
      <div
        className="cv-glow-blob cv-glow-blob--b pointer-events-none absolute -left-20 top-1/3 size-[20rem] opacity-30"
        style={reduced ? { animation: "none" } : undefined}
        aria-hidden
      />

      <div className="relative mx-auto max-w-6xl px-6">
        <motion.div className="mb-16 text-center" {...makeScroll(reduced)}>
          <h2
            id="hiw-heading"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h1)",
              fontWeight: 400,
              lineHeight: 1.15,
              color: "var(--cv-ink)",
            }}
          >
            How it works
          </h2>
          <p
            className="mx-auto mt-3 max-w-md"
            style={{
              color: "var(--cv-ink-muted)",
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-body)",
              lineHeight: 1.6,
            }}
          >
            Five steps from resume upload to a personalized roadmap. The whole flow takes
            under 20 minutes.
          </p>
        </motion.div>

        <ol className="flex flex-col items-start gap-8 lg:flex-row lg:items-start lg:gap-0">
          {howItWorksSteps.map((step, i) => {
            const isLast = i === howItWorksSteps.length - 1

            return (
              <motion.li
                key={step.label}
                className="flex flex-1 flex-row items-start gap-4 lg:flex-col lg:items-center lg:text-center"
                {...makeScroll(reduced, i * 0.09)}
              >
                <div className="flex flex-col items-center lg:w-full lg:flex-row">
                  <motion.div
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
                    style={{
                      background: "var(--cv-accent-muted)",
                      border: "1.5px solid var(--cv-accent)",
                    }}
                    aria-hidden="true"
                    whileHover={
                      reduced
                        ? undefined
                        : { scale: 1.08, transition: { duration: 0.18 } }
                    }
                  >
                    <step.icon
                      className="h-5 w-5"
                      style={{ color: "var(--cv-accent)" }}
                      strokeWidth={1.8}
                    />
                  </motion.div>

                  {!isLast && (
                    <div
                      className="hidden w-full border-t border-dashed lg:block"
                      style={{ borderColor: "rgba(124, 58, 237, 0.28)" }}
                      aria-hidden="true"
                    />
                  )}
                  {!isLast && (
                    <div
                      className="ml-[23px] mt-2 h-8 border-l border-dashed lg:hidden"
                      style={{ borderColor: "rgba(124, 58, 237, 0.28)" }}
                      aria-hidden="true"
                    />
                  )}
                </div>

                <div className="flex flex-col gap-1 pb-2 lg:mt-4 lg:items-center lg:px-2">
                  <span
                    className="mb-1 w-fit rounded-full px-2.5 py-0.5 text-center"
                    style={{
                      background: "var(--cv-accent-muted)",
                      color: "var(--cv-accent)",
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-caption)",
                      fontWeight: 600,
                    }}
                  >
                    Step {i + 1}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--cv-font-serif)",
                      fontSize: "var(--cv-text-h3)",
                      fontWeight: 500,
                      lineHeight: 1.3,
                      color: "var(--cv-ink)",
                    }}
                  >
                    {step.label}
                  </span>
                  <span
                    style={{
                      color: "var(--cv-ink-muted)",
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      lineHeight: 1.5,
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
  const reduced = useReducedMotion()

  return (
    <motion.footer
      className="w-full border-t border-black/[0.06] px-6 py-12"
      style={{ background: "var(--cv-bg)" }}
      aria-label="Site footer"
      {...makeScroll(reduced)}
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-8 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col items-center gap-2 sm:items-start">
          <div className="flex items-baseline gap-1.5">
            <span
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "1.25rem",
                fontWeight: 500,
                color: "var(--cv-ink)",
              }}
            >
              CareerVerse
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-xs font-bold tracking-widest"
              style={{
                color: "var(--cv-accent)",
                background: "var(--cv-accent-muted)",
                fontFamily: "var(--cv-font-sans)",
              }}
            >
              AI
            </span>
          </div>
          <p
            style={{
              color: "var(--cv-ink-muted)",
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              lineHeight: 1.5,
            }}
          >
            Experience the role before choosing your future.
          </p>
        </div>

        <nav aria-label="Footer navigation">
          <ul className="flex flex-wrap justify-center gap-6 sm:justify-end">
            {[
              { label: "Features", href: "#features" },
              { label: "How It Works", href: "#how-it-works" },
              { label: "Sign Up", href: "/signup" },
            ].map(({ label, href }) => (
              <li key={label}>
                <a
                  href={href}
                  className="transition-colors duration-150 hover:text-[var(--cv-ink)] focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
                  style={{
                    color: "var(--cv-ink-muted)",
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
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

      <div className="mx-auto mt-10 max-w-6xl border-t border-black/[0.06] pt-6 text-center">
        <p
          style={{
            color: "var(--cv-ink-muted)",
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
          }}
        >
          © {new Date().getFullYear()} CareerVerse AI. MVP build — not yet in production.
        </p>
      </div>
    </motion.footer>
  )
}

/* ─── Page ───────────────────────────────────────────────────────────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen w-full overflow-x-hidden" style={{ background: "var(--cv-bg)" }}>
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
