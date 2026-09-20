'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

/**
 * ProtectedRoute wraps pages that require (or explicitly forbid) authentication.
 *
 * requireAuth=true  → redirect to /auth/login  if NOT authenticated
 * requireAuth=false → redirect to /dashboard   if IS  authenticated
 *
 * Uses isAuthenticated (token-based) — NOT the user object, which may be null
 * even when the backend session is valid.
 */
export default function ProtectedRoute({ children, requireAuth = true }) {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (loading) return

    if (requireAuth && !isAuthenticated) {
      router.replace('/auth/login')
    } else if (!requireAuth && isAuthenticated) {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, loading, router, requireAuth])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Render nothing while redirect is in-flight
  if (requireAuth && !isAuthenticated) return null
  if (!requireAuth && isAuthenticated) return null

  return children
}
