/**
 * Helpers for the JD-anchored Resume Match Report flow.
 * Reuses existing JobMatch + ResumeReviewReport fields — no new AI calls.
 *
 * Important separation:
 * - pickPrimaryMatch → Resume Match Report only (selected JD as reference)
 * - getCareerRecommendationMatches → Career Matches Top 3 (natural ranking;
 *   never promote / inject the selected JD into Rank 1)
 */

import type { JobMatch, ResumeReviewReport } from "@/types"

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function normalizeTitle(title: string) {
  return title.trim().toLowerCase().replace(/[^a-z0-9]+/g, " ")
}

/**
 * Prefer the match for the user-selected JD (by DB id, then title),
 * otherwise fall back to the rank-1 career recommendation.
 *
 * Used ONLY for the Resume Match Report. Do not use this to reorder
 * Career Matches — that would incorrectly force the selected JD to Rank 1.
 */
export function pickPrimaryMatch(
  matches: JobMatch[],
  options: {
    preferredJobDescriptionIds?: number[]
    preferredRoleTitle?: string | null
  } = {},
): JobMatch {
  const sorted = [...matches].sort((a, b) => a.rank - b.rank)
  if (sorted.length === 0) {
    throw new Error("No career matches available to build a resume match report.")
  }

  const preferredIds = new Set(options.preferredJobDescriptionIds ?? [])
  if (preferredIds.size > 0) {
    const byId = sorted
      .filter((m) => preferredIds.has(m.job_description_id))
      .sort((a, b) => b.match_percent - a.match_percent)
    if (byId[0]) return byId[0]
  }

  const preferredTitle = options.preferredRoleTitle
    ? normalizeTitle(options.preferredRoleTitle)
    : ""
  if (preferredTitle) {
    const exact = sorted.find((m) => normalizeTitle(m.role_title) === preferredTitle)
    if (exact) return exact

    const partial = sorted.find((m) => {
      const t = normalizeTitle(m.role_title)
      return t.includes(preferredTitle) || preferredTitle.includes(t)
    })
    if (partial) return partial
  }

  return sorted[0]
}

export type RankedCareerMatch = JobMatch & { displayRank: 1 | 2 | 3 }

/**
 * Career Matches Top 3 from the Career Recommendation Agent response.
 *
 * Preserves the agent's natural ranking. Does not inject, promote, or
 * require the user-selected JD. Dedupes identical role titles (e.g. an
 * uploaded JD plus a sample with the same title) so Rank 1/2 are not twins.
 */
export function getCareerRecommendationMatches(
  matches: JobMatch[],
  limit = 3,
): RankedCareerMatch[] {
  const sorted = [...matches].sort((a, b) => {
    if (a.rank !== b.rank) return a.rank - b.rank
    return b.match_percent - a.match_percent
  })

  const seenTitles = new Set<string>()
  const unique: JobMatch[] = []
  for (const match of sorted) {
    const key = normalizeTitle(match.role_title)
    if (!key || seenTitles.has(key)) continue
    seenTitles.add(key)
    unique.push(match)
    if (unique.length >= limit) break
  }

  return unique.map((match, index) => ({
    ...match,
    displayRank: (index + 1) as 1 | 2 | 3,
  }))
}

export type MatchDimensionScores = {
  technicalSkillMatch: number
  experienceMatch: number
  educationMatch: number | null
}

/**
 * Compose dimension scores from existing resume-review + JD match signals.
 * These are display aids — not separate AI agent outputs.
 */
export function deriveMatchDimensions(
  match: JobMatch,
  report: ResumeReviewReport | null,
): MatchDimensionScores {
  const gapPenalty = Math.min(28, (match.missing_skills?.length ?? 0) * 4)
  const technicalSkillMatch = clamp(
    Math.round(match.match_percent - gapPenalty * 0.45),
    28,
    98,
  )

  const overall = report?.overall_score ?? match.match_percent
  const experienceMatch = clamp(
    Math.round(match.match_percent * 0.62 + overall * 0.38),
    28,
    98,
  )

  const educationMatch = report
    ? clamp(Math.round(overall * 0.8 + match.match_percent * 0.2), 28, 96)
    : null

  return { technicalSkillMatch, experienceMatch, educationMatch }
}
