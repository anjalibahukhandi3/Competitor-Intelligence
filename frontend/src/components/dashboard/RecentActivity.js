'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Activity, Clock } from 'lucide-react'
import { formatDateTime } from '@/utils/helpers'
import Card from '@/components/ui/Card'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import { monitoringApi } from '@/services/api'

export default function RecentActivity() {
  const router = useRouter()
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRecentActivity = async () => {
      setLoading(true)
      try {
        const res = await monitoringApi.getChanges(6)
        const items = res.data?.items || []
        setActivities(items)
      } catch (err) {
        console.error('Failed to load recent activity:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchRecentActivity()
  }, [])

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-teal-500 rounded-lg flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recent Activity
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Latest monitoring & change events
            </p>
          </div>
        </div>
      </div>

      {/* Activity Feed */}
      {loading ? (
        <SkeletonLoader count={3} height="60px" className="rounded-lg" />
      ) : activities.length === 0 ? (
        <div className="text-center py-6 text-gray-500 text-sm">
          No recent activity detected. Run a monitoring scan to start tracking.
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {activities.map((activity, index) => (
            <motion.div
              key={activity.id || index}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-start space-x-3 group"
            >
              <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Activity className="w-4 h-4" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {activity.summary || activity.event_type || 'Change detected'}
                  </h4>
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 flex-shrink-0 ml-2">
                    <Clock className="w-3 h-3 mr-1" />
                    {formatDateTime(activity.detected_at)}
                  </div>
                </div>

                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Category: {activity.category || 'General'} • Impact:{' '}
                  {activity.impact_level || 'Medium'}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
        <button
          onClick={() => router.push('/monitoring')}
          className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
        >
          View Activity Log
        </button>
      </div>
    </Card>
  )
}