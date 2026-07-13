/**
 * Career Mentor API client.
 *
 * - `getMentorHistory`      — GET  /career-mentor/history/{resume_id}
 * - `streamMentorChat`      — POST /career-mentor/chat         (resume-scoped)
 * - `streamGeneralMentorChat` — POST /career-mentor/chat/general  (no resume needed)
 *
 * Chat endpoints stream Server-Sent Events. Each `data:` line carries a
 * JSON-encoded text chunk; the sentinel `data: [DONE]` signals the end. We
 * use the Fetch API (not EventSource) because EventSource doesn't support
 * POST or custom headers (Bearer token).
 */

import { AUTH_TOKEN_STORAGE_KEY, getApiBaseUrl } from "@/services/api"
import type { MentorHistoryResponse, MentorMessageRecord } from "@/types"

/** Fetch the full conversation history for a resume. */
export async function getMentorHistory(resumeId: number): Promise<MentorMessageRecord[]> {
  const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
  const res = await fetch(`${getApiBaseUrl()}/career-mentor/history/${resumeId}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!res.ok) {
    throw new Error(`Failed to load mentor history: ${res.status}`)
  }

  const data: MentorHistoryResponse = await res.json()
  return data.messages
}

/**
 * Send a message to the Career Mentor and stream the response.
 *
 * @param resumeId  The resume whose context the mentor should use.
 * @param message   The user's message text.
 * @param onChunk   Called with each decoded text chunk as it arrives.
 * @param onDone    Called with the full accumulated text when streaming completes.
 * @param onError   Called with an error message if the stream fails.
 */
export async function streamMentorChat(
  resumeId: number,
  message: string,
  onChunk: (chunk: string) => void,
  onDone: (fullText: string) => void,
  onError: (error: string) => void,
): Promise<void> {
  const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

  let res: Response
  try {
    res = await fetch(`${getApiBaseUrl()}/career-mentor/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ resume_id: resumeId, message }),
    })
  } catch (err) {
    onError("Could not connect to the mentor. Please check your connection.")
    return
  }

  if (!res.ok) {
    onError(`Mentor request failed (${res.status}). Please try again.`)
    return
  }

  const reader = res.body?.getReader()
  if (!reader) {
    onError("Streaming is not supported in this browser. Please upgrade.")
    return
  }

  const decoder = new TextDecoder()
  const accumulated: string[] = []
  let partial = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      partial += decoder.decode(value, { stream: true })

      // SSE lines are separated by "\n\n"; split and process complete events.
      const parts = partial.split("\n\n")
      // The last element may be incomplete — keep it in the buffer.
      partial = parts.pop() ?? ""

      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith("data: ")) continue

        const payload = line.slice(6) // strip "data: "

        if (payload === "[DONE]") {
          onDone(accumulated.join(""))
          return
        }

        try {
          const text: string = JSON.parse(payload)
          accumulated.push(text)
          onChunk(text)
        } catch {
          // Non-JSON payloads are unexpected but harmless — skip.
        }
      }
    }
  } catch (err) {
    onError("The connection was interrupted. Please try again.")
  } finally {
    reader.releaseLock()
  }

  // If we reach here without a [DONE] sentinel, still resolve with what we have.
  onDone(accumulated.join(""))
}

/** Internal SSE streaming helper shared by both chat functions. */
async function _streamSse(
  url: string,
  body: Record<string, unknown>,
  onChunk: (chunk: string) => void,
  onDone: (fullText: string) => void,
  onError: (error: string) => void,
): Promise<void> {
  const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

  let res: Response
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    })
  } catch {
    onError("Could not connect to the mentor. Please check your connection.")
    return
  }

  if (!res.ok) {
    onError("Mentor request failed. Please try again.")
    return
  }

  const reader = res.body?.getReader()
  if (!reader) {
    onError("Streaming is not supported in this browser.")
    return
  }

  const decoder = new TextDecoder()
  const accumulated: string[] = []
  let partial = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      partial += decoder.decode(value, { stream: true })
      const parts = partial.split("\n\n")
      partial = parts.pop() ?? ""
      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith("data: ")) continue
        const payload = line.slice(6)
        if (payload === "[DONE]") {
          onDone(accumulated.join(""))
          return
        }
        try {
          const text: string = JSON.parse(payload)
          accumulated.push(text)
          onChunk(text)
        } catch { /* skip malformed chunks */ }
      }
    }
  } catch {
    onError("The connection was interrupted. Please try again.")
  } finally {
    reader.releaseLock()
  }

  onDone(accumulated.join(""))
}

/**
 * Send a general career question to the mentor (no resume required).
 * Uses the /career-mentor/chat/general endpoint.
 */
export async function streamGeneralMentorChat(
  message: string,
  history: Array<{ role: string; content: string }>,
  onChunk: (chunk: string) => void,
  onDone: (fullText: string) => void,
  onError: (error: string) => void,
): Promise<void> {
  return _streamSse(
    `${getApiBaseUrl()}/career-mentor/chat/general`,
    { message, history },
    onChunk,
    onDone,
    onError,
  )
}
