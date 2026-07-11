import { type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { type ColorVariant } from "@/components/JourneyCard"

/*
 * FeatureCard — landing page marketing card
 *
 * Shares JourneyCard visual DNA (pastel surface, serif title, icon circle)
 * without status chips — those belong to the signed-in journey UI.
 */

const cardBg: Record<ColorVariant, string> = {
  amber: "bg-[#FEF2BF]",
  sage: "bg-[#D4EDD8]",
  sky: "bg-[#D5E8F8]",
  lavender: "bg-[#EDE4FF]",
}

const iconBg: Record<ColorVariant, string> = {
  amber: "bg-[#F6DC6D]",
  sage: "bg-[#9DD4A8]",
  sky: "bg-[#93C6ED]",
  lavender: "bg-[#C4B5FD]",
}

const iconColor: Record<ColorVariant, string> = {
  amber: "text-amber-800",
  sage: "text-green-800",
  sky: "text-sky-800",
  lavender: "text-purple-800",
}

export interface FeatureCardProps {
  title: string
  description: string
  colorVariant: ColorVariant
  icon: LucideIcon
  className?: string
}

export function FeatureCard({
  title,
  description,
  colorVariant,
  icon: Icon,
  className,
}: FeatureCardProps) {
  return (
    <div
      className={cn(
        "flex h-full flex-col gap-3 rounded-[var(--cv-radius-card)] p-5",
        "shadow-[var(--cv-shadow-card)]",
        "transition-shadow duration-200 hover:shadow-[0_8px_24px_0_rgb(17_24_39/0.10)]",
        cardBg[colorVariant],
        className,
      )}
    >
      <div
        className={cn(
          "flex h-11 w-11 shrink-0 items-center justify-center rounded-full",
          iconBg[colorVariant],
        )}
      >
        <Icon className={cn("h-5 w-5", iconColor[colorVariant])} strokeWidth={1.8} />
      </div>

      <div className="flex flex-col gap-1">
        <span
          className="leading-snug text-gray-900"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
          }}
        >
          {title}
        </span>
        <span
          className="text-gray-600"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            lineHeight: 1.5,
          }}
        >
          {description}
        </span>
      </div>
    </div>
  )
}
