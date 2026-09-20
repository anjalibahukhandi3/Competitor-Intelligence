'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  Users,
  Activity,
  Tag,
  Flag,
  Globe,
  PieChart as PieIcon,
} from 'lucide-react'
import Card from '@/components/ui/Card'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import { competitorsApi, monitoringApi } from '@/services/api'

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [competitors, setCompetitors] = useState([])
  const [changes, setChanges] = useState([])

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      setLoading(true)
      try {
        const [compRes, changeRes] = await Promise.all([
          competitorsApi.getAll(1, 100).catch(() => ({ data: { items: [] } })),
          monitoringApi.getChanges(100).catch(() => ({ data: { items: [] } })),
        ])

        const compItems = compRes.data?.items || []
        const changeItems = changeRes.data?.items || []

        setCompetitors(compItems)
        setChanges(changeItems)
      } catch (err) {
        console.error('Failed to load analytics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalyticsData()
  }, [])

  // Aggregate Metrics
  const totalCompetitors = competitors.length
  const activeCompetitors = competitors.filter(
    (c) => c.is_active !== false
  ).length

  // Industry breakdown
  const industryCounts = competitors.reduce((acc, c) => {
    const ind = c.industry?.trim() || 'Unspecified'
    acc[ind] = (acc[ind] || 0) + 1
    return acc
  }, {})

  // Impact level breakdown
  const impactCounts = changes.reduce((acc, ch) => {
    const imp = ch.impact_level || 'Medium'
    acc[imp] = (acc[imp] || 0) + 1
    return acc
  }, {})

  // Category breakdown
  const categoryCounts = changes.reduce((acc, ch) => {
    const cat = ch.category || 'General'
    acc[cat] = (acc[cat] || 0) + 1
    return acc
  }, {})

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-7xl mx-auto pb-12"
    >
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
          Analytics & Market Intelligence
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">
          Dynamic breakdown of monitored competitor profiles and detected change events
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <SkeletonLoader count={6} height="140px" className="rounded-xl" />
        </div>
      ) : (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-5 flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 flex items-center justify-center font-bold">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {totalCompetitors}
                </p>
                <p className="text-xs text-gray-500 font-medium">
                  Tracked Competitors
                </p>
              </div>
            </Card>

            <Card className="p-5 flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 flex items-center justify-center font-bold">
                <Activity className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {activeCompetitors}
                </p>
                <p className="text-xs text-gray-500 font-medium">
                  Active Monitoring
                </p>
              </div>
            </Card>

            <Card className="p-5 flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-orange-50 dark:bg-orange-900/30 text-orange-600 flex items-center justify-center font-bold">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {changes.length}
                </p>
                <p className="text-xs text-gray-500 font-medium">
                  Detected Events
                </p>
              </div>
            </Card>

            <Card className="p-5 flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-purple-50 dark:bg-purple-900/30 text-purple-600 flex items-center justify-center font-bold">
                <PieIcon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {Object.keys(industryCounts).length}
                </p>
                <p className="text-xs text-gray-500 font-medium">
                  Industries Covered
                </p>
              </div>
            </Card>
          </div>

          {/* Breakdown Grids */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Industry Distribution */}
            <Card className="p-6">
              <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Tag className="w-4 h-4 text-blue-500" />
                Industry Distribution
              </h3>
              {Object.keys(industryCounts).length === 0 ? (
                <p className="text-xs text-gray-400">No industry data yet</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(industryCounts).map(([ind, count]) => {
                    const percent = Math.round((count / (totalCompetitors || 1)) * 100)
                    return (
                      <div key={ind} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold text-gray-700 dark:text-gray-300">
                          <span>{ind}</span>
                          <span>{count} ({percent}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-blue-600 h-full rounded-full"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>

            {/* Change Impact Levels */}
            <Card className="p-6">
              <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                Change Impact Breakdown
              </h3>
              {Object.keys(impactCounts).length === 0 ? (
                <p className="text-xs text-gray-400">No change impact events yet</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(impactCounts).map(([imp, count]) => {
                    const percent = Math.round((count / (changes.length || 1)) * 100)
                    return (
                      <div key={imp} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold text-gray-700 dark:text-gray-300">
                          <span>{imp} Impact</span>
                          <span>{count} ({percent}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              imp.toLowerCase() === 'high'
                                ? 'bg-red-500'
                                : imp.toLowerCase() === 'medium'
                                ? 'bg-orange-500'
                                : 'bg-blue-500'
                            }`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>

            {/* Category Breakdown */}
            <Card className="p-6">
              <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-500" />
                Detected Change Categories
              </h3>
              {Object.keys(categoryCounts).length === 0 ? (
                <p className="text-xs text-gray-400">No category events yet</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(categoryCounts).map(([cat, count]) => {
                    const percent = Math.round((count / (changes.length || 1)) * 100)
                    return (
                      <div key={cat} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold text-gray-700 dark:text-gray-300">
                          <span>{cat}</span>
                          <span>{count} ({percent}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-purple-600 h-full rounded-full"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </motion.div>
  )
}