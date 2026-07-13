import { type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { type ColorVariant } from "@/components/JourneyCard"

/*
 * FeatureCard — landing marketing card.
 * Dark elevated surface + violet icon circle; colorVariant is ignored for fill.
 */

export interface FeatureCardProps {
  title: string
  description: string
  colorVariant: ColorVariant
  icon: LucideIcon
  className?: string
  category?: string
}

export function FeatureCard({
  title,
  description,
  icon: Icon,
  className,
  category,
}: FeatureCardProps) {
  return (
    <div
      className={cn(
        "cv-card flex h-full flex-col gap-3 p-6",
        "transition-shadow duration-200 hover:shadow-[var(--cv-shadow-main)]",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="cv-icon-circle">
          <Icon className="h-5 w-5" strokeWidth={1.8} style={{ color: "var(--cv-accent)" }} />
        </div>
        {category && <span className="cv-badge">{category}</span>}
      </div>

      <div className="flex flex-col gap-1.5">
        <span
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
            color: "var(--cv-ink)",
            lineHeight: 1.3,
          }}
        >
          {title}
        </span>
        <span
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            lineHeight: 1.5,
            color: "var(--cv-ink-muted)",
          }}
        >
          {description}
        </span>
      </div>
    </div>
  )
}
