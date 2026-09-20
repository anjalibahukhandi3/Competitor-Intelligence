'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Play,
  RefreshCw,
  Clock,
  Filter,
  Building2,
  Calendar,
  Layers,
  AlertTriangle,
  Globe,
  FileText,
  Settings,
} from 'lucide-react'
import EmptyState from '@/components/ui/EmptyState'
import Button from '@/components/ui/Button'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import ErrorComponent from '@/components/ui/ErrorComponent'
import SnapshotViewModal from '@/components/monitoring/SnapshotViewModal'
import { competitorsApi, monitoringApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState('changes') // 'changes' | 'timeline' | 'frequency'

  // Competitors list
  const [competitors, setCompetitors] = useState([])

  // Changes state
  const [changes, setChanges] = useState([])
  const [loadingChanges, setLoadingChanges] = useState(true)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [impactFilter, setImpactFilter] = useState('')

  // Timeline state
  const [selectedCompetitorId, setSelectedCompetitorId] = useState('')
  const [timelineItems, setTimelineItems] = useState([])
  const [loadingTimeline, setLoadingTimeline] = useState(false)

  // Snapshot modal state
  const [selectedSnapshotId, setSelectedSnapshotId] = useState(null)

  // Trigger monitoring run loading
  const [runningMonitoring, setRunningMonitoring] = useState(false)

  // Frequency updating
  const [updatingFreqId, setUpdatingFreqId] = useState(null)

  // Fetch competitors list
  const fetchCompetitors = useCallback(async () => {
    try {
      const res = await competitorsApi.getAll(1, 100)
      const items = res.data?.items || (Array.isArray(res.data) ? res.data : [])
      setCompetitors(items)
      if (items.length > 0 && !selectedCompetitorId) {
        setSelectedCompetitorId(items[0].id)
      }
      return items
    } catch (err) {
      console.error('Error fetching competitors:', err)
      return []
    }
  }, [selectedCompetitorId])

  // Fetch change events
  const fetchChanges = useCallback(async () => {
    setLoadingChanges(true)
    try {
      const res = await monitoringApi.getChanges(
        50,
        categoryFilter || null,
        impactFilter || null
      )
      const items = res.data?.items || (Array.isArray(res.data) ? res.data : [])
      setChanges(items)
    } catch (err) {
      console.error('Error fetching change events:', err)
    } finally {
      setLoadingChanges(false)
    }
  }, [categoryFilter, impactFilter])

  // Fetch timeline for a specific competitor
  const fetchTimeline = useCallback(async (comp_id) => {
    if (!comp_id) return
    setLoadingTimeline(true)
    try {
      const res = await monitoringApi.getTimeline(comp_id, 50)
      const items = res.data?.items || []
      setTimelineItems(items)
    } catch (err) {
      console.error('Error fetching timeline:', err)
    } finally {
      setLoadingTimeline(false)
    }
  }, [])

  useEffect(() => {
    fetchCompetitors()
  }, [fetchCompetitors])

  useEffect(() => {
    if (activeTab === 'changes') {
      fetchChanges()
    } else if (activeTab === 'timeline' && selectedCompetitorId) {
      fetchTimeline(selectedCompetitorId)
    }
  }, [activeTab, selectedCompetitorId, fetchChanges, fetchTimeline])

  // Trigger manual monitoring run for all competitors
  const handleRunMonitoringAll = async () => {
    setRunningMonitoring(true)
    try {
      const res = await monitoringApi.runMonitoring()
      toast.success(
        `Monitoring run initiated! Enqueued ${res.data?.enqueued_count || 'all active'} targets.`
      )
      fetchChanges()
    } catch (err) {
      console.error('Error running monitoring:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to trigger monitoring run'
      )
    } finally {
      setRunningMonitoring(false)
    }
  }

  // Frequency change handler
  const handleFrequencyChange = async (competitorId, frequency) => {
    setUpdatingFreqId(competitorId)
    try {
      await monitoringApi.updateFrequency(competitorId, frequency)
      toast.success(`Frequency updated to '${frequency}'`)
      fetchCompetitors()
    } catch (err) {
      console.error('Error updating frequency:', err)
      toast.error('Failed to update monitoring frequency')
    } finally {
      setUpdatingFreqId(null)
    }
  }

  const renderImpactBadge = (impact) => {
    const imp = impact?.toLowerCase()
    const styles = {
      high: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200',
      medium:
        'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400 border-orange-200',
      low: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200',
    }
    return (
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${
          styles[imp] || styles.medium
        }`}
      >
        {impact || 'Medium'} Impact
      </span>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-7xl mx-auto pb-12"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
            Monitoring Engine
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">
            Real-time change detection, intelligence timelines & snapshot inspection
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            icon={RefreshCw}
            onClick={() => {
              if (activeTab === 'changes') fetchChanges()
              else if (activeTab === 'timeline') fetchTimeline(selectedCompetitorId)
            }}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            icon={Play}
            iconPosition="left"
            loading={runningMonitoring}
            onClick={handleRunMonitoringAll}
          >
            Run Monitoring Now
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('changes')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'changes'
              ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Activity className="w-4 h-4" />
          Detected Changes Feed
        </button>

        <button
          onClick={() => setActiveTab('timeline')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'timeline'
              ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Competitor Timeline
        </button>

        <button
          onClick={() => setActiveTab('frequency')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'frequency'
              ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Settings className="w-4 h-4" />
          Monitoring Frequencies
        </button>
      </div>

      {/* Tab 1: Detected Changes Feed */}
      {activeTab === 'changes' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-200/70 dark:border-gray-700/70 shadow-sm">
            <div className="flex flex-wrap items-center gap-3">
              <Filter className="w-4 h-4 text-gray-400" />

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="input-field py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 rounded-lg w-auto"
              >
                <option value="">All Categories</option>
                <option value="Pricing">Pricing</option>
                <option value="Features">Features</option>
                <option value="Homepage">Homepage</option>
                <option value="Hiring">Hiring</option>
                <option value="Marketing">Marketing</option>
                <option value="Documentation">Documentation</option>
              </select>

              <select
                value={impactFilter}
                onChange={(e) => setImpactFilter(e.target.value)}
                className="input-field py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 rounded-lg w-auto"
              >
                <option value="">All Impact Levels</option>
                <option value="High">High Impact</option>
                <option value="Medium">Medium Impact</option>
                <option value="Low">Low Impact</option>
              </select>
            </div>

            <div className="text-xs text-gray-500">
              Showing {changes.length} change events
            </div>
          </div>

          {/* Changes Feed List */}
          {loadingChanges ? (
            <SkeletonLoader count={5} height="90px" className="rounded-xl" />
          ) : changes.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No change events detected"
              description="Click 'Run Monitoring Now' above to spawn automated web scrapers and detect competitor website changes."
              action={
                <Button
                  variant="primary"
                  icon={Play}
                  loading={runningMonitoring}
                  onClick={handleRunMonitoringAll}
                >
                  Run Monitoring Scan
                </Button>
              }
              className="py-16"
            />
          ) : (
            <div className="space-y-3">
              {changes.map((change) => (
                <motion.div
                  key={change.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700/70 shadow-sm hover:shadow-md transition-all flex items-start justify-between gap-4"
                >
                  <div className="flex items-start space-x-3.5 flex-1 min-w-0">
                    <div className="w-9 h-9 rounded-lg bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 flex items-center justify-center flex-shrink-0 font-bold mt-0.5">
                      <Activity className="w-4 h-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                          {change.category || 'General'}
                        </span>
                        {renderImpactBadge(change.impact_level)}
                      </div>

                      <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mt-1">
                        {change.summary || change.event_type || 'Website update detected'}
                      </h4>

                      {change.metadata && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                          {typeof change.metadata === 'object'
                            ? JSON.stringify(change.metadata)
                            : String(change.metadata)}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="text-xs text-gray-400 flex items-center flex-shrink-0">
                    <Clock className="w-3 h-3 mr-1" />
                    {change.detected_at
                      ? new Date(change.detected_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : 'Recently'}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Competitor Timeline */}
      {activeTab === 'timeline' && (
        <div className="space-y-4">
          {/* Competitor Picker */}
          {competitors.length > 0 && (
            <div className="p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-200/70 dark:border-gray-700/70 shadow-sm flex items-center space-x-3">
              <Building2 className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Select Competitor Timeline:
              </span>
              <select
                value={selectedCompetitorId}
                onChange={(e) => setSelectedCompetitorId(e.target.value)}
                className="input-field py-1.5 px-3 text-sm bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 rounded-lg w-auto"
              >
                {competitors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.company_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {loadingTimeline ? (
            <SkeletonLoader count={4} height="80px" className="rounded-xl" />
          ) : timelineItems.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No timeline events recorded"
              description="No snapshots, changes, or reports exist for this competitor yet."
              className="py-16"
            />
          ) : (
            <div className="relative pl-6 border-l-2 border-primary-200 dark:border-primary-900/50 space-y-6 my-4">
              {timelineItems.map((item, idx) => {
                const isSnapshot = item.event_type === 'snapshot' || item.snapshot_id
                const isReport = item.event_type === 'report' || item.report_id

                return (
                  <motion.div
                    key={item.id || idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="relative"
                  >
                    <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-primary-600 border-4 border-white dark:border-gray-900 shadow" />

                    <div className="p-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700/70 shadow-sm flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center space-x-2">
                          {isSnapshot ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                              <Globe className="w-3 h-3 mr-1" /> Snapshot
                            </span>
                          ) : isReport ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                              <FileText className="w-3 h-3 mr-1" /> Report
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
                              <Activity className="w-3 h-3 mr-1" /> Change Event
                            </span>
                          )}

                          <span className="text-xs text-gray-400">
                            {item.timestamp
                              ? new Date(item.timestamp).toLocaleString()
                              : 'Recently'}
                          </span>
                        </div>

                        <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mt-1">
                          {item.title || item.event_type}
                        </h4>
                        {item.description && (
                          <p className="text-xs text-gray-600 dark:text-gray-300 mt-0.5">
                            {item.description}
                          </p>
                        )}
                      </div>

                      {item.snapshot_id && (
                        <Button
                          variant="outline"
                          size="sm"
                          icon={Globe}
                          onClick={() => setSelectedSnapshotId(item.snapshot_id)}
                        >
                          Inspect Snapshot
                        </Button>
                      )}
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Monitoring Frequencies */}
      {activeTab === 'frequency' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {competitors.map((comp) => (
              <div
                key={comp.id}
                className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200/80 dark:border-gray-700/80 shadow-sm space-y-4"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 flex items-center justify-center font-bold">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100">
                      {comp.company_name}
                    </h4>
                    <p className="text-xs text-gray-500 truncate max-w-[200px]">
                      {comp.website}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">
                    Scan Frequency
                  </label>
                  <select
                    defaultValue="daily"
                    disabled={updatingFreqId === comp.id}
                    onChange={(e) =>
                      handleFrequencyChange(comp.id, e.target.value)
                    }
                    className="input-field text-xs bg-gray-50 dark:bg-gray-700/50"
                  >
                    <option value="realtime">Realtime (Every hour)</option>
                    <option value="daily">Daily (Every 24 hours)</option>
                    <option value="weekly">Weekly (Every 7 days)</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Snapshot View Modal */}
      <SnapshotViewModal
        isOpen={Boolean(selectedSnapshotId)}
        onClose={() => setSelectedSnapshotId(null)}
        snapshotId={selectedSnapshotId}
      />
    </motion.div>
  )
}