import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

export function ProtectedRoute({
  allow,
  loading = false,
  children,
}: PropsWithChildren<{ allow: boolean; loading?: boolean }>) {
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0b1d3a] text-white">
        Проверяем вход...
      </div>
    )
  }

  if (!allow) return <Navigate to="/auth" replace />
  return <>{children}</>
}
