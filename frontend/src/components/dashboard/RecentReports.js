'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { FileText, Download, Eye, Calendar, Sparkles } from 'lucide-react'
import { formatDate } from '@/utils/helpers'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import SkeletonLoader from '@/components/ui/SkeletonLoader'
import { competitorsApi, reportsApi } from '@/services/api'
import ReportViewModal from '@/components/reports/ReportViewModal'
import toast from 'react-hot-toast'

export default function RecentReports() {
  const router = useRouter()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [viewingReportId, setViewingReportId] = useState(null)
  const [viewingCompName, setViewingCompName] = useState('Competitor')
  const [downloadingId, setDownloadingId] = useState(null)

  useEffect(() => {
    const fetchRecentReports = async () => {
      setLoading(true)
      try {
        const compRes = await competitorsApi.getAll(1, 20)
        const comps = compRes.data?.items || []

        if (comps.length === 0) {
          setReports([])
          setLoading(false)
          return
        }

        const recent = []
        for (const comp of comps) {
          try {
            const res = await reportsApi.listForCompetitor(comp.id, 1, 5)
            const items = res.data?.items || []
            const mapped = items.map((r) => ({
              ...r,
              competitor_name: comp.company_name,
            }))
            recent.push(...mapped)
          } catch (err) {
            console.error(`Error loading reports for ${comp.company_name}`, err)
          }
        }

        recent.sort(
          (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
        )
        setReports(recent.slice(0, 4))
      } catch (err) {
        console.error('Error in RecentReports:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchRecentReports()
  }, [])

  const handleDownload = async (reportId, compName) => {
    setDownloadingId(reportId)
    try {
      const res = await reportsApi.download(reportId)
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${compName}_report_${reportId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Report PDF downloaded!')
    } catch (err) {
      toast.error('Failed to download PDF report')
    } finally {
      setDownloadingId(null)
    }
  }

  const getStatusBadge = (status) => {
    const s = status?.toLowerCase() || 'pending'
    const badges = {
      completed:
        'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      processing:
        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      pending:
        'bg-stone-200 text-stone-700 dark:bg-stone-700/40 dark:text-stone-300',
      failed:
        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    }

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          badges[s] || badges.pending
        }`}
      >
        {s.charAt(0).toUpperCase() + s.slice(1)}
      </span>
    )
  }

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recent Reports
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Your latest competitor analysis reports
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push('/reports')}
        >
          View All
        </Button>
      </div>

      {/* Reports List */}
      {loading ? (
        <SkeletonLoader count={3} height="70px" className="rounded-lg" />
      ) : reports.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
          <Sparkles className="w-8 h-8 mx-auto text-purple-400 mb-2 opacity-60" />
          No reports generated yet. Trigger a report from Competitors or Reports page.
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report, index) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/30 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-10 h-10 bg-white dark:bg-gray-700 rounded-lg flex items-center justify-center shadow-sm">
                  <FileText className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {report.competitor_name} AI Report
                  </h4>
                  <div className="flex items-center space-x-2 mt-1">
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {report.competitor_name}
                    </p>
                    <span className="text-xs text-gray-400">•</span>
                    <p className="text-xs text-gray-500">
                      ID: {report.id.substring(0, 8)}...
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 mt-2">
                    {getStatusBadge(report.status)}
                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <Calendar className="w-3 h-3 mr-1" />
                      {formatDate(report.created_at)}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={Eye}
                  onClick={() => {
                    setViewingReportId(report.id)
                    setViewingCompName(report.competitor_name)
                  }}
                />
                {report.status === 'completed' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Download}
                    loading={downloadingId === report.id}
                    onClick={() =>
                      handleDownload(report.id, report.competitor_name)
                    }
                  />
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/reports')}
        >
          View All Reports
        </Button>
      </div>

      <ReportViewModal
        isOpen={Boolean(viewingReportId)}
        onClose={() => setViewingReportId(null)}
        reportId={viewingReportId}
        competitorName={viewingCompName}
      />
    </Card>
  )
}