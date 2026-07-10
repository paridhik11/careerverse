import type { ReactNode } from "react"
import { motion } from "framer-motion"

/**
 * Shared visual shell for the Login and Signup pages: centered floating card
 * on the app's warm canvas background, branded header, and a footer slot for
 * the "switch between login/signup" link.
 */
export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}) {
  return (
    <div
      className="flex min-h-screen w-full items-center justify-center px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-sm rounded-[1.5rem] bg-white p-8"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div className="mb-6 text-center">
          <span
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "1.25rem",
              fontWeight: 500,
              color: "#111827",
            }}
          >
            CareerVerse
          </span>
          <span
            className="ml-1 align-super text-[10px] font-semibold tracking-wider"
            style={{ color: "var(--cv-accent)", fontFamily: "var(--cv-font-sans)" }}
          >
            AI
          </span>
        </div>

        <h1
          className="mb-1 text-center text-gray-900"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h2)",
            fontWeight: 400,
          }}
        >
          {title}
        </h1>
        <p
          className="mb-6 text-center text-gray-500"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
        >
          {subtitle}
        </p>

        {children}

        <p
          className="mt-6 text-center text-gray-500"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
        >
          {footer}
        </p>
      </motion.div>
    </div>
  )
}
