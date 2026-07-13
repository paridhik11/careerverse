/**
 * ScoreRing — a circular SVG gauge that displays a 0–100 score.
 *
 * Design decisions:
 *  - SVG stroke-dasharray/dashoffset technique for the ring fill.
 *  - CSS transition animates the fill on mount (no Framer Motion needed here
 *    since the animation is a simple value change, not a layout animation).
 *  - `color` and `trackColor` are intentionally props so each usage site can
 *    pick the right palette token without hard-coding colors here.
 *  - The score number uses Fraunces serif to match headings throughout the app.
 *
 * Usage:
 *  <ScoreRing score={85} label="Overall" color="#6B7FFF" size={96} />
 */

import { useEffect, useState } from "react"

interface ScoreRingProps {
  /** 0–100 score value. */
  score: number
  /** Label shown below the number (e.g. "Overall" or "ATS"). */
  label: string
  /** Ring fill color. */
  color: string
  /** Ring track (background circle) color. Defaults to light gray. */
  trackColor?: string
  /** Outer diameter in px. Defaults to 96. */
  size?: number
  /** Stroke width in px. Defaults to 8. */
  strokeWidth?: number
}

export function ScoreRing({
  score,
  label,
  color,
  trackColor = "rgba(255, 255, 255, 0.12)",
  size = 96,
  strokeWidth = 8,
}: ScoreRingProps) {
  const [animated, setAnimated] = useState(false)

  useEffect(() => {
    // Defer to the next frame so the CSS transition has a start value to
    // interpolate from (dashoffset starts at full circumference = "empty").
    const id = requestAnimationFrame(() => setAnimated(true))
    return () => cancelAnimationFrame(id)
  }, [])

  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const filledLength = (score / 100) * circumference
  const offset = circumference - filledLength

  return (
    <div className="flex flex-col items-center gap-2">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-label={`${label} score: ${score} out of 100`}
        role="img"
      >
        {/* Track ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        {/* Fill ring — starts from 12 o'clock position */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={animated ? offset : circumference}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 900ms cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
        {/* Score number */}
        <text
          x="50%"
          y="50%"
          dominantBaseline="central"
          textAnchor="middle"
          fill="var(--cv-ink)"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: size * 0.25,
            fontWeight: 500,
          }}
        >
          {score}
        </text>
      </svg>

      <span
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          fontWeight: 600,
          color: "var(--cv-ink-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {label}
      </span>
    </div>
  )
}
