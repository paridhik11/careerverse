/**
 * CareerTilesIntro — full-screen animated intro section for the Landing Page.
 *
 * An original implementation inspired by the Motion Tiles framer template.
 * Features:
 *   - Two infinite-scroll columns of career tiles drifting upward.
 *   - One column moves slower (parallax effect).
 *   - Tiles fade in with stagger on mount.
 *   - Each tile has a glassmorphism surface, icon, role name, and department.
 *   - A radial gradient vignette fades the tiles at top/bottom edges.
 *   - Central hero text overlaid above the tile columns.
 *   - "Scroll to explore" indicator at the bottom.
 *   - Respects prefers-reduced-motion (tiles become static opacity fade).
 */

import { useReducedMotion, motion, useMotionValue } from "framer-motion"
import { useEffect, useRef } from "react"
import {
  Code2,
  Layout,
  Server,
  Layers,
  Brain,
  BarChart3,
  Database,
  Package,
  Palette,
  Monitor,
  Shield,
  Smartphone,
  Gamepad2,
  Cloud,
  ChevronDown,
} from "lucide-react"

/* ─── Career tile data ──────────────────────────────────────────────────── */

interface CareerTile {
  role: string
  dept: string
  Icon: React.ComponentType<{ size?: number; strokeWidth?: number; color?: string }>
  accent: string
}

const CAREER_TILES: CareerTile[] = [
  { role: "Software Engineer",    dept: "Engineering",  Icon: Code2,        accent: "#8B7CFF" },
  { role: "Frontend Engineer",    dept: "Engineering",  Icon: Layout,       accent: "#A78BFA" },
  { role: "Backend Engineer",     dept: "Engineering",  Icon: Server,       accent: "#818CF8" },
  { role: "Full Stack Engineer",  dept: "Engineering",  Icon: Layers,       accent: "#7C3AED" },
  { role: "AI Engineer",          dept: "AI/ML",        Icon: Brain,        accent: "#C4B5FD" },
  { role: "ML Engineer",          dept: "AI/ML",        Icon: Brain,        accent: "#A855F7" },
  { role: "Data Scientist",       dept: "Data",         Icon: BarChart3,    accent: "#8B7CFF" },
  { role: "Data Analyst",         dept: "Data",         Icon: Database,     accent: "#6366F1" },
  { role: "Product Manager",      dept: "Product",      Icon: Package,      accent: "#A78BFA" },
  { role: "UX Designer",          dept: "Design",       Icon: Palette,      accent: "#C084FC" },
  { role: "UI Designer",          dept: "Design",       Icon: Monitor,      accent: "#E879F9" },
  { role: "DevOps Engineer",      dept: "Infra",        Icon: Cloud,        accent: "#818CF8" },
  { role: "Cloud Engineer",       dept: "Infra",        Icon: Cloud,        accent: "#6366F1" },
  { role: "Cybersecurity Analyst",dept: "Security",     Icon: Shield,       accent: "#7C3AED" },
  { role: "Mobile Developer",     dept: "Mobile",       Icon: Smartphone,   accent: "#A78BFA" },
  { role: "Game Developer",       dept: "Gaming",       Icon: Gamepad2,     accent: "#8B7CFF" },
]

// Duplicate for seamless scroll
const LEFT_TILES = [...CAREER_TILES.slice(0, 8), ...CAREER_TILES.slice(0, 8)]
const RIGHT_TILES = [...CAREER_TILES.slice(8), ...CAREER_TILES.slice(8)]

/* ─── Individual tile component ─────────────────────────────────────────── */

function TileCard({ tile, index }: { tile: CareerTile; index: number }) {
  const { Icon } = tile
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
      className="w-52 flex-shrink-0 rounded-2xl p-4"
      style={{
        background: "rgba(20, 18, 31, 0.75)",
        border: "1px solid rgba(255,255,255,0.10)",
        backdropFilter: "blur(10px)",
        boxShadow: "0 4px 24px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.04) inset",
      }}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex size-9 shrink-0 items-center justify-center rounded-xl"
          style={{ background: `${tile.accent}22` }}
        >
          <Icon size={17} strokeWidth={1.8} color={tile.accent} />
        </div>
        <div className="min-w-0">
          <p
            className="truncate"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "var(--cv-ink)",
              lineHeight: 1.3,
            }}
          >
            {tile.role}
          </p>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "0.6875rem",
              fontWeight: 500,
              color: tile.accent,
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              marginTop: "2px",
            }}
          >
            {tile.dept}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

/* ─── Scrolling column ───────────────────────────────────────────────────── */

interface ScrollColumnProps {
  tiles: CareerTile[]
  speed: number        // pixels per second (negative = scroll up)
  reduced: boolean | null
}

function ScrollColumn({ tiles, speed, reduced }: ScrollColumnProps) {
  const y = useMotionValue(0)
  const rafRef = useRef<number>(0)
  const prevTimeRef = useRef<number | null>(null)
  const totalHeightRef = useRef(0)

  // Calculate total height of one set (half of duplicated array)
  const tileHeight = 76 // card height + gap
  const halfCount = tiles.length / 2
  totalHeightRef.current = halfCount * tileHeight

  useEffect(() => {
    if (reduced) return

    let position = 0

    function tick(timestamp: number) {
      if (prevTimeRef.current === null) {
        prevTimeRef.current = timestamp
      }
      const delta = (timestamp - prevTimeRef.current) / 1000
      prevTimeRef.current = timestamp

      position += speed * delta

      // Reset when one full set has scrolled past (seamless loop)
      const total = totalHeightRef.current
      if (Math.abs(position) >= total) {
        position = position % total
      }

      y.set(position)
      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [speed, reduced, y])

  return (
    <motion.div
      className="flex flex-col gap-3"
      style={{ y: reduced ? 0 : y }}
    >
      {tiles.map((tile, i) => (
        <TileCard key={`${tile.role}-${i}`} tile={tile} index={i % (tiles.length / 2)} />
      ))}
    </motion.div>
  )
}

/* ─── Main component ─────────────────────────────────────────────────────── */

export function CareerTilesIntro() {
  const reduced = useReducedMotion()

  return (
    <section
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden"
      style={{ background: "var(--cv-bg)" }}
      aria-label="Career paths overview"
    >
      {/* ── Ambient glow ─────────────────────────────────────────────────── */}
      <div
        className="pointer-events-none absolute inset-0 z-0"
        aria-hidden
      >
        <div
          className="absolute left-1/2 top-1/2 size-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(139,124,255,0.18) 0%, transparent 70%)",
          }}
        />
      </div>

      {/* ── Tile columns ─────────────────────────────────────────────────── */}
      <div
        className="pointer-events-none absolute inset-0 z-0 flex items-start justify-center gap-4 pt-4"
        aria-hidden
      >
        {/* Left column — slower */}
        <div className="flex flex-col gap-3 opacity-60">
          <ScrollColumn
            tiles={LEFT_TILES}
            speed={reduced ? 0 : -28}
            reduced={reduced}
          />
        </div>

        {/* Spacer for centre hero content */}
        <div className="w-[380px] flex-shrink-0" />

        {/* Right column — faster */}
        <div className="flex flex-col gap-3 opacity-60">
          <ScrollColumn
            tiles={RIGHT_TILES}
            speed={reduced ? 0 : -42}
            reduced={reduced}
          />
        </div>
      </div>

      {/* ── Top vignette ─────────────────────────────────────────────────── */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 z-[1] h-48"
        style={{
          background: "linear-gradient(to bottom, var(--cv-bg) 0%, transparent 100%)",
        }}
        aria-hidden
      />

      {/* ── Bottom vignette ──────────────────────────────────────────────── */}
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 z-[1] h-56"
        style={{
          background: "linear-gradient(to top, var(--cv-bg) 0%, transparent 100%)",
        }}
        aria-hidden
      />

      {/* ── Hero text ────────────────────────────────────────────────────── */}
      <motion.div
        className="relative z-10 flex flex-col items-center gap-6 px-4 text-center"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="cv-badge"
          style={{ fontSize: "0.75rem", letterSpacing: "0.1em" }}
        >
          AI Career Intelligence
        </motion.div>

        {/* Headline */}
        <motion.h2
          className="max-w-lg"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "clamp(2rem, 5vw, 3rem)",
            fontWeight: 400,
            lineHeight: 1.1,
            letterSpacing: "-0.02em",
            color: "var(--cv-ink)",
          }}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
        >
          Every career path,{" "}
          <span
            style={{
              background: "linear-gradient(100deg, #8B7CFF 0%, #C4B5FD 55%, #F5F3FF 100%)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              WebkitTextFillColor: "transparent",
              color: "transparent",
            }}
          >
            uniquely yours.
          </span>
        </motion.h2>

        {/* Sub-copy */}
        <motion.p
          className="max-w-sm"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.7,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          Upload your resume, discover where you fit, experience it first-hand,
          and get a roadmap to get there.
        </motion.p>

        {/* CTA */}
        <motion.a
          href="/signup"
          className="inline-flex items-center gap-2 rounded-full px-7 py-3.5 font-semibold"
          style={{
            background: "linear-gradient(135deg, #8B7CFF 0%, #A78BFA 55%, #C4B5FD 100%)",
            color: "#0B0A14",
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            boxShadow: "0 8px 28px rgba(139,124,255,0.40)",
          }}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
          whileHover={{ scale: 1.04, transition: { duration: 0.15 } }}
          whileTap={{ scale: 0.97 }}
        >
          Find Your Path
        </motion.a>

        {/* Role count */}
        <motion.p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            color: "var(--cv-ink-muted)",
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.6 }}
        >
          16 career paths · AI-matched to your resume
        </motion.p>
      </motion.div>

      {/* ── Scroll indicator ─────────────────────────────────────────────── */}
      <motion.div
        className="absolute bottom-8 left-1/2 z-10 flex -translate-x-1/2 flex-col items-center gap-1"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.5 }}
        aria-hidden
      >
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "0.6875rem",
            fontWeight: 500,
            color: "var(--cv-ink-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
          }}
        >
          Scroll
        </p>
        <motion.div
          animate={{ y: [0, 5, 0] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
        >
          <ChevronDown size={16} strokeWidth={2} style={{ color: "var(--cv-ink-muted)" }} />
        </motion.div>
      </motion.div>
    </section>
  )
}
