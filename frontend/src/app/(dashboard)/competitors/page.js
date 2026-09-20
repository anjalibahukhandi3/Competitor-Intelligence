'use client'

import CompetitorCard from '@/components/competitors/CompetitorCard'
import CompetitorModal from '@/components/competitors/CompetitorModal'
import CompetitorViewModal from '@/components/competitors/CompetitorViewModal'
import Button from '@/components/ui/Button'
import ConfirmModal from '@/components/ui/ConfirmModal'
import EmptyState from '@/components/ui/EmptyState'
import ErrorComponent from '@/components/ui/ErrorComponent'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import { competitorsApi, monitoringApi, reportsApi } from '@/services/api'
import { AnimatePresence, motion } from 'framer-motion'
import { Plus, RefreshCw, Search, Users } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'

export default function CompetitorsPage() {
  const [competitors, setCompetitors] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Modal States
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCompetitor, setEditingCompetitor] = useState(null)

  const [viewingCompetitor, setViewingCompetitor] = useState(null)

  const [deletingCompetitor, setDeletingCompetitor] = useState(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  // Fetch competitors from backend
  const fetchCompetitors = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await competitorsApi.getAll(1, 100)
      const data = response.data
      const items = data.items || (Array.isArray(data) ? data : [])
      setCompetitors(items)
      setTotal(data.total ?? items.length)
    } catch (err) {
      console.error('Failed to load competitors:', err)
      setError(
        err.response?.data?.detail ||
        'Failed to load competitors list. Please verify server connection.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCompetitors()
  }, [fetchCompetitors])

  // Open modal to add a new competitor
  const handleOpenAddModal = () => {
    setEditingCompetitor(null)
    setIsModalOpen(true)
  }

  // Open modal to edit an existing competitor
  const handleOpenEditModal = (competitor) => {
    setEditingCompetitor(competitor)
    setIsModalOpen(true)
  }

  // Handle View details
  const handleViewCompetitor = (competitor) => {
    setViewingCompetitor(competitor)
  }

  // Handle Delete trigger
  const handlePromptDelete = (competitor) => {
    setDeletingCompetitor(competitor)
  }

  const handleConfirmDelete = async () => {
    if (!deletingCompetitor) return
    setDeleteLoading(true)
    try {
      await competitorsApi.delete(deletingCompetitor.id)
      toast.success(
        `'${deletingCompetitor.company_name}' removed from competitors`
      )
      setDeletingCompetitor(null)
      fetchCompetitors()
    } catch (err) {
      console.error('Failed to delete competitor:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to delete competitor'
      )
    } finally {
      setDeleteLoading(false)
    }
  }

  // Handle Generate Report
  const handleGenerateReport = async (competitor) => {
    try {
      await reportsApi.triggerReport(competitor.id)
      toast.success(`Report generation triggered for ${competitor.company_name}`)
    } catch (err) {
      console.error('Failed to trigger report:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to trigger report generation'
      )
    }
  }

  // Handle Monitor Now
  const handleMonitorNow = async (competitor) => {
    try {
      await monitoringApi.triggerForCompetitor(competitor.id)
      toast.success(`Monitoring scan initiated for ${competitor.company_name}`)
    } catch (err) {
      console.error('Failed to trigger monitoring scan:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to trigger monitoring scan'
      )
    }
  }

  // Filter competitors by search query
  const filteredCompetitors = competitors.filter((c) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      c.company_name?.toLowerCase().includes(q) ||
      c.website?.toLowerCase().includes(q) ||
      c.industry?.toLowerCase().includes(q) ||
      c.country?.toLowerCase().includes(q)
    )
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-7xl mx-auto pb-12"
    >
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
            Competitors
            {!loading && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400 border border-primary-200/50 dark:border-primary-800/40">
                {total} Total
              </span>
            )}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">
            Manage, track, and monitor competitor intelligence profiles
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            icon={RefreshCw}
            onClick={fetchCompetitors}
            disabled={loading}
            title="Refresh list"
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            icon={Plus}
            iconPosition="left"
            onClick={handleOpenAddModal}
          >
            Add Competitor
          </Button>
        </div>
      </div>

      {/* Search & Filter Bar (shown when list has or had items) */}
      {competitors.length > 0 && (
        <div className="flex items-center justify-between gap-4 p-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200/70 dark:border-gray-700/70 shadow-sm">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by company name, website, or industry..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-transparent border-none focus:outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400"
            />
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-400 pr-3 hidden sm:block">
            Showing {filteredCompetitors.length} of {competitors.length}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 py-4">
          <SkeletonLoader count={6} height="180px" className="rounded-xl" />
        </div>
      ) : error ? (
        <ErrorComponent
          title="Error Loading Competitors"
          message={error}
          onRetry={fetchCompetitors}
        />
      ) : competitors.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No competitors yet"
          description="Add your first competitor to start monitoring their activities, website changes, and generating AI insights."
          action={
            <Button
              variant="primary"
              icon={Plus}
              iconPosition="left"
              onClick={handleOpenAddModal}
            >
              Add Your First Competitor
            </Button>
          }
          className="py-20"
        />
      ) : filteredCompetitors.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400 font-medium">
            No competitors match your search filter &quot;{searchQuery}&quot;
          </p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSearchQuery('')}
            className="mt-3"
          >
            Clear Search
          </Button>
        </div>
      ) : (
        <AnimatePresence mode="popLayout">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCompetitors.map((competitor) => (
              <CompetitorCard
                key={competitor.id}
                competitor={competitor}
                onView={handleViewCompetitor}
                onEdit={handleOpenEditModal}
                onDelete={handlePromptDelete}
                onGenerateReport={handleGenerateReport}
                onMonitorNow={handleMonitorNow}
              />
            ))}
          </div>
        </AnimatePresence>
      )}

      {/* Add / Edit Form Modal */}
      <CompetitorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        competitor={editingCompetitor}
        onSuccess={fetchCompetitors}
      />

      {/* Detail View Modal */}
      <CompetitorViewModal
        isOpen={Boolean(viewingCompetitor)}
        onClose={() => setViewingCompetitor(null)}
        competitor={viewingCompetitor}
        onEdit={handleOpenEditModal}
        onGenerateReport={handleGenerateReport}
        onMonitorNow={handleMonitorNow}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(deletingCompetitor)}
        onClose={() => setDeletingCompetitor(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Competitor?"
        message={`Are you sure you want to remove '${deletingCompetitor?.company_name}'? All associated monitoring data will be deleted.`}
        confirmText="Delete Competitor"
        loading={deleteLoading}
        variant="danger"
      />
    </motion.div>
  )
}