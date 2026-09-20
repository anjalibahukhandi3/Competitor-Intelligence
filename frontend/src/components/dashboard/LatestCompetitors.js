'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Users, Globe, Activity, Plus } from 'lucide-react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import CompetitorModal from '@/components/competitors/CompetitorModal'
import { competitorsApi } from '@/services/api'

export default function LatestCompetitors() {
  const router = useRouter()
  const [competitors, setCompetitors] = useState([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const fetchCompetitors = async () => {
    setLoading(true)
    try {
      const res = await competitorsApi.getAll(1, 4)
      const items = res.data?.items || (Array.isArray(res.data) ? res.data : [])
      setCompetitors(items)
    } catch (err) {
      console.error('Error fetching latest competitors:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCompetitors()
  }, [])

  const getStatusBadge = (isActive) => {
    const active = isActive !== false
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
          active
            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
        }`}
      >
        {active ? 'Active' : 'Inactive'}
      </span>
    )
  }

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-teal-500 to-emerald-500 rounded-lg flex items-center justify-center">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Latest Competitors
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Recently added to intelligence tracking
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          icon={Plus}
          onClick={() => setIsModalOpen(true)}
        >
          Add
        </Button>
      </div>

      {/* Competitors List */}
      {loading ? (
        <SkeletonLoader count={3} height="60px" className="rounded-lg" />
      ) : competitors.length === 0 ? (
        <div className="text-center py-6 text-gray-500 text-sm">
          No competitors added yet.
        </div>
      ) : (
        <div className="space-y-4">
          {competitors.map((competitor, index) => {
            const letter = competitor.company_name
              ? competitor.company_name.charAt(0).toUpperCase()
              : 'C'
            const domain = competitor.website
              ? competitor.website.replace(/^https?:\/\//, '')
              : 'N/A'

            return (
              <motion.div
                key={competitor.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => router.push('/competitors')}
                className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700/30 rounded-lg transition-colors cursor-pointer group"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-amber-500 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-sm">
                    {letter}
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-600 transition-colors">
                      {competitor.company_name}
                    </h4>
                    <div className="flex items-center space-x-2 mt-1 truncate">
                      <div className="flex items-center text-xs text-gray-600 dark:text-gray-400 truncate">
                        <Globe className="w-3 h-3 mr-1 flex-shrink-0" />
                        <span className="truncate">{domain}</span>
                      </div>
                      {competitor.industry && (
                        <>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-600 dark:text-gray-400 truncate">
                            {competitor.industry}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end space-y-1 ml-2">
                  {getStatusBadge(competitor.is_active)}
                  <div className="flex items-center text-xs text-gray-400">
                    <Activity className="w-3 h-3 mr-1" />
                    Tracked
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Button
          variant="ghost"
          size="sm"
          className="w-full"
          onClick={() => router.push('/competitors')}
        >
          View All Competitors
        </Button>
      </div>

      <CompetitorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchCompetitors}
      />
    </Card>
  )
}