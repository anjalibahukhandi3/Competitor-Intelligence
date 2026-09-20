'use client'

import { useState, useEffect } from 'react'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import {
  FileText,
  Download,
  Calendar,
  CheckCircle,
  Clock,
  AlertTriangle,
  Zap,
  TrendingUp,
  ShieldAlert,
  Target,
  ListChecks,
} from 'lucide-react'
import { reportsApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function ReportViewModal({
  isOpen,
  onClose,
  reportId,
  competitorName = 'Competitor',
}) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    if (!isOpen || !reportId) return

    const fetchReport = async () => {
      setLoading(true)
      try {
        const res = await reportsApi.getById(reportId)
        setReport(res.data)
      } catch (err) {
        console.error('Failed to load report:', err)
        toast.error('Failed to load report details')
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
  }, [isOpen, reportId])

  const handleDownload = async () => {
    if (!reportId) return
    setDownloading(true)
    try {
      const response = await reportsApi.download(reportId)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `competitor_report_${reportId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Report PDF downloaded successfully!')
    } catch (err) {
      console.error('Download failed:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to download PDF report'
      )
    } finally {
      setDownloading(false)
    }
  }

  if (!isOpen) return null

  const renderStatusBadge = (status) => {
    const s = status?.toLowerCase() || 'pending'
    const styles = {
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
        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${
          styles[s] || styles.pending
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

  const formattedDate = report?.created_at
    ? new Date(report.created_at).toLocaleString()
    : 'N/A'

  const swot = report?.swot_analysis || {}

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`AI Report: ${competitorName}`}
      subtitle={`Generated on ${formattedDate}`}
      icon={FileText}
      maxWidth="max-w-3xl"
    >
      {loading ? (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" />
          <p className="text-sm text-gray-500">Loading intelligence report...</p>
        </div>
      ) : !report ? (
        <div className="py-10 text-center text-gray-500">
          Report data unavailable.
        </div>
      ) : (
        <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-1">
          {/* Status & Header Info */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700">
            <div className="space-y-1">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 block">
                Report ID: {report.id}
              </span>
              <div className="flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-300">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formattedDate}</span>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {renderStatusBadge(report.status)}
              {report.status === 'completed' && (
                <Button
                  variant="primary"
                  size="sm"
                  icon={Download}
                  loading={downloading}
                  onClick={handleDownload}
                >
                  Download PDF
                </Button>
              )}
            </div>
          </div>

          {/* Executive Summary */}
          {report.executive_summary && (
            <div className="p-4 rounded-xl bg-blue-50/70 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/40">
              <h4 className="text-sm font-bold text-blue-900 dark:text-blue-200 mb-2 flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-blue-600" />
                Executive Summary
              </h4>
              <p className="text-sm text-blue-950 dark:text-blue-300 leading-relaxed whitespace-pre-line">
                {report.executive_summary}
              </p>
            </div>
          )}

          {/* SWOT Matrix */}
          {(swot.strengths || swot.weaknesses || swot.opportunities || swot.threats) && (
            <div>
              <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-1.5">
                <Target className="w-4 h-4 text-primary-500" />
                SWOT Analysis
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-green-50/60 dark:bg-green-900/20 border border-green-200/60 dark:border-green-800/40">
                  <h5 className="text-xs font-bold text-green-800 dark:text-green-300 mb-1.5">
                    Strengths
                  </h5>
                  <p className="text-xs text-green-900 dark:text-green-400 whitespace-pre-line leading-relaxed">
                    {Array.isArray(swot.strengths) ? swot.strengths.join('\n') : swot.strengths || 'N/A'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-red-50/60 dark:bg-red-900/20 border border-red-200/60 dark:border-red-800/40">
                  <h5 className="text-xs font-bold text-red-800 dark:text-red-300 mb-1.5">
                    Weaknesses
                  </h5>
                  <p className="text-xs text-red-900 dark:text-red-400 whitespace-pre-line leading-relaxed">
                    {Array.isArray(swot.weaknesses) ? swot.weaknesses.join('\n') : swot.weaknesses || 'N/A'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/60 dark:bg-purple-900/20 border border-purple-200/60 dark:border-purple-800/40">
                  <h5 className="text-xs font-bold text-purple-800 dark:text-purple-300 mb-1.5">
                    Opportunities
                  </h5>
                  <p className="text-xs text-purple-900 dark:text-purple-400 whitespace-pre-line leading-relaxed">
                    {Array.isArray(swot.opportunities) ? swot.opportunities.join('\n') : swot.opportunities || 'N/A'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-900/20 border border-amber-200/60 dark:border-amber-800/40">
                  <h5 className="text-xs font-bold text-amber-800 dark:text-amber-300 mb-1.5">
                    Threats
                  </h5>
                  <p className="text-xs text-amber-900 dark:text-amber-400 whitespace-pre-line leading-relaxed">
                    {Array.isArray(swot.threats) ? swot.threats.join('\n') : swot.threats || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Positioning & Pricing Changes */}
          {(report.positioning_changes || report.pricing_changes) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {report.positioning_changes && (
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-700">
                  <h4 className="text-xs font-bold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-indigo-500" />
                    Positioning Changes
                  </h4>
                  <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                    {report.positioning_changes}
                  </p>
                </div>
              )}

              {report.pricing_changes && (
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-700">
                  <h4 className="text-xs font-bold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                    Pricing Changes
                  </h4>
                  <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                    {report.pricing_changes}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Strategic Threats & Action Items */}
          {report.strategic_threats && (
            <div className="p-4 rounded-xl bg-orange-50/50 dark:bg-orange-900/20 border border-orange-200/50 dark:border-orange-800/40">
              <h4 className="text-xs font-bold text-orange-900 dark:text-orange-200 mb-2 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-orange-600" />
                Strategic Threats
              </h4>
              <p className="text-xs text-orange-950 dark:text-orange-300 leading-relaxed whitespace-pre-line">
                {report.strategic_threats}
              </p>
            </div>
          )}

          {report.action_items && (
            <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-900/20 border border-emerald-200/50 dark:border-emerald-800/40">
              <h4 className="text-xs font-bold text-emerald-900 dark:text-emerald-200 mb-2 flex items-center gap-1.5">
                <ListChecks className="w-4 h-4 text-emerald-600" />
                Recommended Action Items
              </h4>
              <p className="text-xs text-emerald-950 dark:text-emerald-300 leading-relaxed whitespace-pre-line">
                {Array.isArray(report.action_items)
                  ? report.action_items.join('\n• ')
                  : report.action_items}
              </p>
            </div>
          )}

          {/* Footer actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-100 dark:border-gray-700/60">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
