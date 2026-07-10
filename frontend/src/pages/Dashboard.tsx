import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/useAuth"

/**
 * Placeholder only — proves PrivateRoute + the login/signup redirect work.
 * The real dashboard (resume score, career matches, roadmap, etc.) is built
 * in a later milestone.
 */
export function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div
      className="flex min-h-screen w-full flex-col items-center justify-center gap-4 px-4 text-center"
      style={{ background: "var(--cv-bg)" }}
    >
      <p
        style={{
          fontFamily: "var(--cv-font-serif)",
          fontSize: "var(--cv-text-h1)",
          fontWeight: 400,
          color: "#111827",
        }}
      >
        Logged in as {user?.email}
      </p>
      <p
        className="text-gray-500"
        style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
      >
        The full dashboard ships in a later milestone.
      </p>
      <Button variant="outline" onClick={logout}>
        Log out
      </Button>
    </div>
  )
}
