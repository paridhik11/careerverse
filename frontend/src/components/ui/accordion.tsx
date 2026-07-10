/**
 * Accordion — a shadcn-style wrapper around Radix UI's Accordion primitive.
 * Used in the ATS Analysis section of the Resume Report page.
 *
 * Design system alignment:
 *  - Rounded corners from --cv-radius-card
 *  - Manrope body text
 *  - Subtle hover/focus states matching the rest of the UI
 */

import * as React from "react"
import { Accordion } from "radix-ui"
import { ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"

const AccordionRoot = Accordion.Root
const AccordionItem = React.forwardRef<
  React.ComponentRef<typeof Accordion.Item>,
  React.ComponentPropsWithoutRef<typeof Accordion.Item>
>(({ className, ...props }, ref) => (
  <Accordion.Item
    ref={ref}
    className={cn("border-b border-black/[0.06] last:border-0", className)}
    {...props}
  />
))
AccordionItem.displayName = "AccordionItem"

const AccordionTrigger = React.forwardRef<
  React.ComponentRef<typeof Accordion.Trigger>,
  React.ComponentPropsWithoutRef<typeof Accordion.Trigger>
>(({ className, children, ...props }, ref) => (
  <Accordion.Header className="flex">
    <Accordion.Trigger
      ref={ref}
      className={cn(
        "group flex flex-1 items-center justify-between py-4 text-left outline-none",
        "transition-all duration-150",
        "focus-visible:ring-2 focus-visible:ring-[var(--cv-accent)] focus-visible:ring-offset-2 rounded-sm",
        className,
      )}
      style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", fontWeight: 600, color: "#111827" }}
      {...props}
    >
      {children}
      <ChevronDown
        size={16}
        strokeWidth={2}
        className="shrink-0 text-gray-500 transition-transform duration-200 group-data-[state=open]:rotate-180"
        aria-hidden
      />
    </Accordion.Trigger>
  </Accordion.Header>
))
AccordionTrigger.displayName = "AccordionTrigger"

const AccordionContent = React.forwardRef<
  React.ComponentRef<typeof Accordion.Content>,
  React.ComponentPropsWithoutRef<typeof Accordion.Content>
>(({ className, children, ...props }, ref) => (
  <Accordion.Content
    ref={ref}
    className="overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
    {...props}
  >
    <div
      className={cn("pb-4 pt-0", className)}
      style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#4B5563", lineHeight: 1.6 }}
    >
      {children}
    </div>
  </Accordion.Content>
))
AccordionContent.displayName = "AccordionContent"

export { AccordionRoot, AccordionItem, AccordionTrigger, AccordionContent }
