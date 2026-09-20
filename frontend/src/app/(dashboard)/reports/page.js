'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  Plus,
  Building2,
  Download,
  Eye,
  RefreshCw,
  Calendar,
  CheckCircle,
  Clock,
  AlertTriangle,
} from 'lucide-react'
import EmptyState from '@/components/ui/EmptyState'
import Button from '@/components/ui/Button'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import ErrorComponent from '@/components/ui/ErrorComponent'
import ReportTriggerModal from '@/components/reports/ReportTriggerModal'
import ReportViewModal from '@/components/reports/ReportViewModal'
import { competitorsApi, reportsApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function ReportsPage() {
  const [competitors, setCompetitors] = useState([])
  const [selectedCompetitorId, setSelectedCompetitorId] = useState('all')
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Modals
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState(false)
  const [selectedReportId, setSelectedReportId] = useState(null)
  const [viewingCompetitorName, setViewingCompetitorName] = useState('Competitor')
  const [downloadingId, setDownloadingId] = useState(null)

  // 1. Fetch competitors
  const fetchCompetitors = useCallback(async () => {
    try {
      const res = await competitorsApi.getAll(1, 100)
      const items = res.data?.items || (Array.isArray(res.data) ? res.data : [])
      setCompetitors(items)
      return items
    } catch (err) {
      console.error('Error fetching competitors:', err)
      return []
    }
  }, [])

  // 2. Fetch reports for selected competitor or all competitors
  const fetchReports = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      let comps = competitors
      if (comps.length === 0) {
        comps = await fetchCompetitors()
      }

      if (comps.length === 0) {
        setReports([])
        setLoading(false)
        return
      }

      let targetComps = comps
      if (selectedCompetitorId !== 'all') {
        targetComps = comps.filter((c) => c.id === selectedCompetitorId)
      }

      const allReports = []
      for (const comp of targetComps) {
        try {
          const res = await reportsApi.listForCompetitor(comp.id, 1, 20)
          const items = res.data?.items || (Array.isArray(res.data) ? res.data : [])
          const mapped = items.map((r) => ({
            ...r,
            competitor_name: comp.company_name,
            competitor_website: comp.website,
          }))
          allReports.push(...mapped)
        } catch (err) {
          console.error(`Failed loading reports for ${comp.company_name}:`, err)
        }
      }

      // Sort newest first
      allReports.sort(
        (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
      )
      setReports(allReports)
    } catch (err) {
      console.error('Error listing reports:', err)
      setError('Failed to fetch intelligence reports. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [competitors, selectedCompetitorId, fetchCompetitors])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  const handleDownload = async (reportId, compName) => {
    setDownloadingId(reportId)
    try {
      const response = await reportsApi.download(reportId)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute(
        'download',
        `${compName.replace(/\s+/g, '_')}_report_${reportId}.pdf`
      )
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Report PDF downloaded successfully!')
    } catch (err) {
      console.error('Download failed:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to download report PDF file'
      )
    } finally {
      setDownloadingId(null)
    }
  }

  const handleViewReport = (report) => {
    setSelectedReportId(report.id)
    setViewingCompetitorName(report.competitor_name || 'Competitor')
  }

  const renderStatusBadge = (status) => {
    const s = status?.toLowerCase() || 'pending'
    const badges = {
      completed:
        'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200',
      processing:
        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200',
      pending:
        'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200',
      failed:
        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200',
    }

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
          badges[s] || badges.pending
        }`}
      >
        {s === 'completed' && <CheckCircle className="w-3 h-3 mr-1" />}
        {s === 'processing' && <Clock className="w-3 h-3 mr-1 animate-spin" />}
        {s === 'pending' && <Clock className="w-3 h-3 mr-1" />}
        {s === 'failed' && <AlertTriangle className="w-3 h-3 mr-1" />}
        {s.toUpperCase()}
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
            Intelligence Reports
            {!loading && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400 border border-purple-200/50">
                {reports.length} Reports
              </span>
            )}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">
            AI-generated deep-dive analysis reports & downloadable PDFs
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            icon={RefreshCw}
            onClick={fetchReports}
            disabled={loading}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            icon={Plus}
            iconPosition="left"
            onClick={() => setIsTriggerModalOpen(true)}
          >
            Generate Report
          </Button>
        </div>
      </div>

      {/* Competitor Selector Filter */}
      {competitors.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-200/70 dark:border-gray-700/70 shadow-sm">
          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <Building2 className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Filter by Competitor:
            </span>
            <select
              value={selectedCompetitorId}
              onChange={(e) => setSelectedCompetitorId(e.target.value)}
              className="input-field py-1.5 px-3 text-sm bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 rounded-lg"
            >
              <option value="all">All Competitors ({competitors.length})</option>
              {competitors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.company_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-4">
          <SkeletonLoader count={4} height="160px" className="rounded-xl" />
        </div>
      ) : error ? (
        <ErrorComponent
          title="Error Loading Reports"
          message={error}
          onRetry={fetchReports}
        />
      ) : reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No reports generated"
          description="Generate your first competitor analysis report to get AI-driven SWOT insights, positioning updates, and PDF downloads."
          action={
            <Button
              variant="primary"
              icon={Plus}
              iconPosition="left"
              onClick={() => setIsTriggerModalOpen(true)}
            >
              Generate Your First Report
            </Button>
          }
          className="py-20"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {reports.map((report) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200/80 dark:border-gray-700/80 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                        {report.competitor_name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        ID: {report.id.substring(0, 8)}...
                      </p>
                    </div>
                  </div>

                  {renderStatusBadge(report.status)}
                </div>

                {report.executive_summary && (
                  <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 mb-4 leading-relaxed bg-gray-50 dark:bg-gray-700/30 p-2.5 rounded-lg border border-gray-100 dark:border-gray-700">
                    {report.executive_summary}
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-gray-100 dark:border-gray-700/60 flex items-center justify-between text-xs">
                <div className="flex items-center text-gray-400 dark:text-gray-500">
                  <Calendar className="w-3.5 h-3.5 mr-1" />
                  {report.created_at
                    ? new Date(report.created_at).toLocaleDateString()
                    : 'Recently'}
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={Eye}
                    onClick={() => handleViewReport(report)}
                  >
                    View
                  </Button>

                  {report.status === 'completed' && (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={Download}
                      loading={downloadingId === report.id}
                      onClick={() =>
                        handleDownload(report.id, report.competitor_name)
                      }
                    >
                      PDF
                    </Button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Report Trigger Modal */}
      <ReportTriggerModal
        isOpen={isTriggerModalOpen}
        onClose={() => setIsTriggerModalOpen(false)}
        onSuccess={fetchReports}
      />

      {/* Report Detail Modal */}
      <ReportViewModal
        isOpen={Boolean(selectedReportId)}
        onClose={() => setSelectedReportId(null)}
        reportId={selectedReportId}
        competitorName={viewingCompetitorName}
      />
    </motion.div>
  )
}