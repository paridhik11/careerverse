/**
 * LandingPage — public marketing surface for CareerVerse AI.
 *
 * Uses the app-wide dark palette (--cv-bg/--cv-ink/--cv-accent/.cv-card,
 * etc. in index.css) shared by every other page. The only Landing-exclusive
 * extras are the gradient headline treatment and the ambient drifting orbs,
 * scoped under .cv-landing.
 *
 * Motion (5 effects, all with a static/opacity-only fallback under
 * prefers-reduced-motion):
 *   1. Hero headline — word-by-word fade + slide-up, staggerChildren.
 *   2. Hero CTA buttons — magnetic hover (useMotionValue + useSpring).
 *   3. Feature cards — staggered scroll-triggered reveal, triggerOnce.
 *   4. Ambient background orbs — slow 16-20s drift behind hero content.
 *   5. Final CTA section — scale + fade entrance on scroll.
 */

import {
  useReducedMotion,
  motion,
  useMotionValue,
  useSpring,
  type Variants,
} from "framer-motion"
import type { ReactNode, MouseEvent as ReactMouseEvent } from "react"
import { FileText, Briefcase, Sparkles, Users, Map, ArrowRight } from "lucide-react"
import { FeatureCard } from "@/components/FeatureCard"
import { CareerTilesIntro } from "@/components/CareerTilesIntro"

/* ─── Animation tokens ───────────────────────────────────────────────────── */

const EASE = [0.22, 1, 0.36, 1] as const

/** Scroll-triggered reveal used by feature cards and section headings.
 *  Reduced-motion fallback is an opacity-only fade — never fully static. */
function makeScroll(reduced: boolean | null, delay = 0) {
  if (reduced) {
    return {
      initial: { opacity: 0 },
      whileInView: { opacity: 1 },
      viewport: { once: true, margin: "-80px" },
      transition: { duration: 0.4, ease: EASE },
    }
  }
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

/** Word-by-word stagger for the hero headline specifically. */
const headlineWordStagger: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06, delayChildren: 0.15 },
  },
}

const headlineWordItem: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: EASE },
  },
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

/* ─── Feature card data ──────────────────────────────────────────────────── */

const features = [
  {
    title: "Resume Review",
    description:
      "Scores your resume against ATS criteria and surfaces specific improvements for your target role.",
    colorVariant: "amber" as const,
    category: "Resume",
    icon: FileText,
  },
  {
    title: "Career Match Explorer",
    description:
      "Compares your resume against the job descriptions you upload and ranks your top 3 career fits by match percentage.",
    colorVariant: "sage" as const,
    category: "Match",
    icon: Briefcase,
  },
  {
    title: "AI Job Simulation",
    description:
      "Drops you into a realistic workplace scenario for your chosen career — 5–10 conversational turns of actual role experience.",
    colorVariant: "lavender" as const,
    category: "Experience",
    icon: Sparkles,
  },
  {
    title: "Career Mentor",
    description:
      "Answers your career questions using your own resume data, match analysis, and simulation results — grounded in your context only.",
    colorVariant: "lavender" as const,
    category: "Mentor",
    icon: Users,
  },
  {
    title: "Learning Roadmap",
    description:
      "Builds a 3-month plan with weekly goals, curated resources, and practice tasks based on your specific skill gaps.",
    colorVariant: "sky" as const,
    category: "Roadmap",
    icon: Map,
  },
]

/* ─── Ambient background orbs (animation #4) ────────────────────────────── */

function AmbientOrbs({ reduced }: { reduced: boolean | null }) {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden" aria-hidden>
      <div
        className="cv-landing-orb cv-landing-orb--a -left-28 -top-20 size-[26rem] md:size-[32rem]"
        style={reduced ? { animation: "none" } : undefined}
      />
      <div
        className="cv-landing-orb cv-landing-orb--b -right-24 top-[18%] size-[22rem] md:size-[28rem]"
        style={reduced ? { animation: "none" } : undefined}
      />
      <div
        className="cv-landing-orb cv-landing-orb--c bottom-[-12%] left-[38%] size-[18rem] md:size-[24rem]"
        style={reduced ? { animation: "none" } : undefined}
      />
    </div>
  )
}

/* ─── Hero CTA with magnetic hover (animation #2) ────────────────────────── */

function MagneticCta({
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
  const MAX_OFFSET = 10
  const PULL_STRENGTH = 0.35

  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const springX = useSpring(x, { stiffness: 220, damping: 20, mass: 0.3 })
  const springY = useSpring(y, { stiffness: 220, damping: 20, mass: 0.3 })

  function handleMouseMove(event: ReactMouseEvent<HTMLAnchorElement>) {
    if (reduced) return
    const rect = event.currentTarget.getBoundingClientRect()
    const relX = event.clientX - (rect.left + rect.width / 2)
    const relY = event.clientY - (rect.top + rect.height / 2)
    x.set(clamp(relX * PULL_STRENGTH, -MAX_OFFSET, MAX_OFFSET))
    y.set(clamp(relY * PULL_STRENGTH, -MAX_OFFSET, MAX_OFFSET))
  }

  function handleMouseLeave() {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.a
      href={href}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="inline-flex items-center gap-2 rounded-full px-7 py-3.5 font-semibold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
      style={{
        background: isPrimary
          ? "linear-gradient(135deg, #8B7CFF 0%, #A78BFA 55%, #C4B5FD 100%)"
          : "rgba(255,255,255,0.06)",
        color: isPrimary ? "#0B0A14" : "var(--cv-ink)",
        border: isPrimary ? "none" : "1px solid rgba(255,255,255,0.14)",
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-body)",
        boxShadow: isPrimary ? "0 10px 30px rgba(139,124,255,0.35)" : undefined,
        x: reduced ? 0 : springX,
        y: reduced ? 0 : springY,
      }}
      whileHover={reduced ? undefined : { scale: 1.03, transition: { duration: 0.18, ease: EASE } }}
      whileTap={reduced ? undefined : { scale: 0.97 }}
    >
      {children}
    </motion.a>
  )
}

/* ─── Navbar ─────────────────────────────────────────────────────────────── */

function Navbar() {
  return (
    <header
      className="sticky top-0 z-50 w-full border-b"
      style={{
        background: "rgba(11, 10, 20, 0.78)",
        borderColor: "rgba(255,255,255,0.06)",
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
              color: "var(--cv-accent-2)",
              background: "var(--cv-accent-soft)",
              fontFamily: "var(--cv-font-sans)",
            }}
          >
            AI
          </span>
        </a>

        <nav className="hidden items-center gap-8 sm:flex" aria-label="Main navigation">
          <a
            href="#features"
            className="transition-colors duration-150 hover:text-[var(--cv-ink)] focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 500,
              color: "var(--cv-ink-muted)",
            }}
          >
            Features
          </a>
        </nav>

        <a
          href="/signup"
          className="rounded-full px-5 py-2.5 font-semibold transition-opacity duration-150 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
          style={{
            background: "var(--cv-accent)",
            color: "#FFFFFF",
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

const heroLineOne = ["Discover.", "Experience."]
const heroLineTwo = ["Build", "Your", "Career."]

function HeroSection() {
  const reduced = useReducedMotion()

  return (
    <section
      className="relative isolate flex min-h-[90svh] flex-col items-center justify-center overflow-hidden px-6 py-24 text-center"
      aria-labelledby="hero-headline"
      style={{ background: "var(--cv-bg)" }}
    >
      <AmbientOrbs reduced={reduced} />

      <motion.div
        className="relative z-[1] mx-auto flex max-w-4xl flex-col items-center"
        variants={reduced ? undefined : heroStagger}
        initial={reduced ? { opacity: 0 } : "hidden"}
        animate={reduced ? { opacity: 1 } : "visible"}
        transition={reduced ? { duration: 0.5, ease: EASE } : undefined}
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
              color: "var(--cv-accent-2)",
              background: "var(--cv-accent-soft)",
              borderRadius: 9999,
              padding: "0.2rem 0.55rem",
            }}
          >
            AI
          </span>
        </motion.p>

        {/* Animation #1: hero headline, word-by-word fade + slide-up */}
        <motion.h1
          id="hero-headline"
          className="cv-landing-gradient-text max-w-4xl"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-display)",
            fontWeight: 400,
            lineHeight: 1.08,
            letterSpacing: "-0.02em",
          }}
          variants={reduced ? undefined : headlineWordStagger}
          initial={reduced ? { opacity: 0 } : "hidden"}
          animate={reduced ? { opacity: 1 } : "visible"}
          transition={reduced ? { duration: 0.5, ease: EASE, delay: 0.1 } : undefined}
        >
          {heroLineOne.map((word, i) => (
            <motion.span
              key={`l1-${i}`}
              variants={reduced ? undefined : headlineWordItem}
              style={{ display: "inline-block", marginRight: "0.28em" }}
            >
              {word}
            </motion.span>
          ))}
          <br className="hidden sm:block" />
          {heroLineTwo.map((word, i) => (
            <motion.span
              key={`l2-${i}`}
              variants={reduced ? undefined : headlineWordItem}
              style={{ display: "inline-block", marginRight: "0.28em" }}
            >
              {word}
            </motion.span>
          ))}
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
          <MagneticCta href="/signup" reduced={reduced}>
            Start Exploring
            <ArrowRight className="h-4 w-4" strokeWidth={2} />
          </MagneticCta>
          <MagneticCta href="#features" variant="secondary" reduced={reduced}>
            See Features
          </MagneticCta>
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
      style={{ background: "var(--cv-bg)" }}
      {...makeScroll(reduced)}
    >
      <motion.div className="mb-14 text-center" {...makeScroll(reduced)}>
        <h2
          id="features-heading"
          className="cv-landing-gradient-text"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            lineHeight: 1.15,
            display: "inline-block",
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

      {/* Animation #3: staggered scroll-triggered card reveal, triggerOnce */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {topRow.map((card, i) => (
          <motion.div
            key={card.title}
            {...makeScroll(reduced, i * 0.1)}
            whileHover={
              reduced
                ? undefined
                : { y: -6, transition: { duration: 0.2, ease: EASE } }
            }
            style={{ willChange: "transform" }}
          >
            <FeatureCard {...card} category={card.category} className="h-full" />
          </motion.div>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:mx-auto lg:max-w-[calc(66.666%+0.5rem)]">
        {bottomRow.map((card, i) => (
          <motion.div
            key={card.title}
            {...makeScroll(reduced, (topRow.length + i) * 0.1)}
            whileHover={
              reduced
                ? undefined
                : { y: -6, transition: { duration: 0.2, ease: EASE } }
            }
            style={{ willChange: "transform" }}
          >
            <FeatureCard {...card} category={card.category} className="h-full" />
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}

/* ─── Final CTA ──────────────────────────────────────────────────────────── */

function FinalCtaSection() {
  const reduced = useReducedMotion()

  return (
    <section
      className="relative w-full overflow-hidden px-6 py-28"
      aria-labelledby="final-cta-heading"
      style={{ background: "var(--cv-bg)" }}
    >
      <div
        className="cv-landing-orb cv-landing-orb--a left-1/2 top-1/2 size-[34rem] -translate-x-1/2 -translate-y-1/2"
        style={reduced ? { animation: "none" } : undefined}
        aria-hidden
      />

      {/* Animation #5: final CTA — scale + fade entrance, more pronounced
          than the feature-card reveals since it's the closing moment. */}
      <motion.div
        className="relative z-[1] mx-auto flex max-w-2xl flex-col items-center text-center"
        initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.9 }}
        whileInView={reduced ? { opacity: 1 } : { opacity: 1, scale: 1 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: reduced ? 0.5 : 0.7, ease: EASE }}
      >
        <h2
          id="final-cta-heading"
          className="cv-landing-gradient-text"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            lineHeight: 1.15,
            display: "inline-block",
          }}
        >
          The future of work is Kinetic.
        </h2>
        <p
          className="mx-auto mt-4 max-w-md"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            lineHeight: 1.7,
            color: "var(--cv-ink-muted)",
          }}
        >
          Stop guessing your next move. Let AI map the path, simulate the role, and show
          you exactly what it takes to get there.
        </p>
        <div className="mt-9">
          <a
            href="/signup"
            className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 font-semibold transition-opacity duration-150 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--cv-accent)]"
            style={{
              background: "linear-gradient(135deg, #8B7CFF 0%, #A78BFA 55%, #C4B5FD 100%)",
              color: "#0B0A14",
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-body)",
              boxShadow: "0 10px 30px rgba(139,124,255,0.35)",
            }}
          >
            Get Started
            <ArrowRight className="h-4 w-4" strokeWidth={2} />
          </a>
        </div>
      </motion.div>
    </section>
  )
}

/* ─── Footer ─────────────────────────────────────────────────────────────── */

function Footer() {
  const reduced = useReducedMotion()

  return (
    <motion.footer
      className="w-full border-t px-6 py-12"
      style={{ background: "var(--cv-bg)", borderColor: "rgba(255,255,255,0.06)" }}
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
                color: "var(--cv-accent-2)",
                background: "var(--cv-accent-soft)",
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

      <div
        className="mx-auto mt-10 max-w-6xl border-t pt-6 text-center"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
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
    <div
      className="cv-landing min-h-screen w-full overflow-x-hidden"
      style={{ background: "var(--cv-bg)" }}
    >
      <Navbar />
      <main>
        {/* Animated career tiles intro — full screen before the hero */}
        <CareerTilesIntro />
        <HeroSection />
        <FeaturesSection />
        <FinalCtaSection />
      </main>
      <Footer />
    </div>
  )
}
