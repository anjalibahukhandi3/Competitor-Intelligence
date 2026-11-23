'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import Link from 'next/link'
import { Radar } from 'lucide-react'

export default function AuthLayout({ children }) {
  return (
    <ProtectedRoute requireAuth={false}>
      <div className="auth-shell min-h-screen">
        <Link href="/" className="auth-brand fixed left-5 top-5 z-10 inline-flex items-center gap-2.5 rounded-full px-3 py-2 text-sm font-bold tracking-tight text-slate-800 transition hover:bg-white/80 sm:left-8 sm:top-7">
          <span className="brand-mark h-8 w-8 rounded-xl"><Radar className="h-4 w-4" /></span>
          <span>Competitor<span className="hidden text-slate-500 sm:inline"> Intelligence</span></span>
        </Link>
        <div className="min-h-screen flex items-center justify-center px-4 pb-10 pt-24 sm:px-6 sm:py-20">
          <div className="w-full max-w-[440px]">
            {children}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
