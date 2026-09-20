'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function AuthLayout({ children }) {
  return (
    <ProtectedRoute requireAuth={false}>
      <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="min-h-screen flex items-center justify-center px-4 py-12">
          <div className="w-full max-w-md">
            {children}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}