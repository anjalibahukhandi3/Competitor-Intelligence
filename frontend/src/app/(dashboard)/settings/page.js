'use client'

import { motion } from 'framer-motion'
import { Palette, Shield, Bell, UserRound } from 'lucide-react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { useTheme } from '@/contexts/ThemeContext'

export default function SettingsPage() {
  const { isDark, changeTheme } = useTheme()

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-5xl space-y-6 pb-12">
      <header>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Manage the preferences currently supported by this workspace.</p>
      </header>

      <Card className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <span className="rounded-xl bg-primary-50 p-3 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300"><Palette className="h-5 w-5" /></span>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-gray-100">Appearance</h2>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Current mode: {isDark ? 'Dark' : 'Light'}.</p>
            </div>
          </div>
          <Button variant="outline" onClick={() => changeTheme(isDark ? 'light' : 'dark')}>Switch to {isDark ? 'light' : 'dark'} mode</Button>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">Account features</h2>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">These settings need backend support before changes can be saved.</p>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {[
            [UserRound, 'Profile management'],
            [Bell, 'Notification preferences'],
            [Shield, 'Password and security'],
          ].map(([Icon, title]) => (
            <div key={title} className="rounded-xl border border-gray-200 p-4 dark:border-gray-700">
              <Icon className="mb-3 h-5 w-5 text-gray-500" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Not available yet</p>
            </div>
          ))}
        </div>
      </Card>
    </motion.div>
  )
}
