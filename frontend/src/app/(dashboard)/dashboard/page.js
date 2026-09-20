'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Users,
  Activity,
  FileText,
  TrendingUp,
  Plus,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import StatsCard from '@/components/dashboard/StatsCard'
import RecentReports from '@/components/dashboard/RecentReports'
import LatestCompetitors from '@/components/dashboard/LatestCompetitors'
import RecentActivity from '@/components/dashboard/RecentActivity'
import QuickActions from '@/components/dashboard/QuickActions'
import AnalyticsChart from '@/components/dashboard/AnalyticsChart'
import Button from '@/components/ui/Button'
import CompetitorModal from '@/components/competitors/CompetitorModal'
import { competitorsApi, monitoringApi, reportsApi } from '@/services/api'

export default function DashboardPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

  const [statsData, setStatsData] = useState({
    totalCompetitors: 0,
    activeMonitoring: 0,
    reportsCount: 0,
    changesCount: 0,
    loading: true,
  })

  const fetchDashboardStats = useCallback(async () => {
    try {
      const [compRes, changeRes] = await Promise.all([
        competitorsApi.getAll(1, 100).catch(() => ({ data: { items: [], total: 0 } })),
        monitoringApi.getChanges(50).catch(() => ({ data: { items: [], total: 0 } })),
      ])

      const comps = compRes.data?.items || []
      const totalComp = compRes.data?.total ?? comps.length
      const activeCount = comps.filter((c) => c.is_active !== false).length

      const changes = changeRes.data?.items || []
      const changesCount = changeRes.data?.total ?? changes.length

      // Count reports across competitors
      let reportsCount = 0
      for (const c of comps.slice(0, 10)) {
        try {
          const repRes = await reportsApi.listForCompetitor(c.id, 1, 1)
          reportsCount += repRes.data?.total ?? 0
        } catch {
          // Ignore error for individual competitor list
        }
      }

      setStatsData({
        totalCompetitors: totalComp,
        activeMonitoring: activeCount,
        reportsCount: reportsCount,
        changesCount: changesCount,
        loading: false,
      })
    } catch (err) {
      console.error('Error fetching dashboard stats:', err)
      setStatsData((prev) => ({ ...prev, loading: false }))
    }
  }, [])

  useEffect(() => {
    fetchDashboardStats()
  }, [fetchDashboardStats])

  const stats = [
    {
      label: 'Total Competitors',
      value: String(statsData.totalCompetitors),
      change: statsData.totalCompetitors > 0 ? 'Active' : '0',
      changeType: 'positive',
      icon: Users,
      color: 'blue',
    },
    {
      label: 'Active Monitoring',
      value: String(statsData.activeMonitoring),
      change: `${statsData.activeMonitoring} Live`,
      changeType: 'positive',
      icon: Activity,
      color: 'green',
    },
    {
      label: 'Reports Generated',
      value: String(statsData.reportsCount),
      change: 'AI SWOT',
      changeType: 'positive',
      icon: FileText,
      color: 'purple',
    },
    {
      label: 'Recent Changes',
      value: String(statsData.changesCount),
      change: 'Detected',
      changeType: 'positive',
      icon: TrendingUp,
      color: 'orange',
    },
  ]

  const userNameDisplay = user?.email
    ? user.email.split('@')[0]
    : 'User'

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
            Welcome back, {userNameDisplay}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Here&apos;s what&apos;s happening with your competitor intelligence today.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center space-x-3"
        >
          <Button
            icon={Plus}
            iconPosition="left"
            onClick={() => setIsAddModalOpen(true)}
          >
            Add Competitor
          </Button>
        </motion.div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {stats.map((stat, index) => (
          <StatsCard key={stat.label} {...stat} delay={index * 0.1} />
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Analytics Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <AnalyticsChart />
          </motion.div>

          {/* Recent Reports */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <RecentReports />
          </motion.div>
        </div>

        {/* Right Column */}
        <div className="space-y-8">
          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <QuickActions />
          </motion.div>

          {/* Latest Competitors */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <LatestCompetitors />
          </motion.div>

          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <RecentActivity />
          </motion.div>
        </div>
      </div>

      <CompetitorModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          fetchDashboardStats()
          router.push('/competitors')
        }}
      />
    </div>
  )
}