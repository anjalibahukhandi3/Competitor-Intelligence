'use client'

import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import {
  Building2,
  Globe,
  Tag,
  Flag,
  Calendar,
  Activity,
  FileText,
  RefreshCw,
  Edit,
  ExternalLink,
} from 'lucide-react'

export default function CompetitorViewModal({
  isOpen,
  onClose,
  competitor,
  onEdit,
  onGenerateReport,
  onMonitorNow,
}) {
  if (!competitor) return null

  const formattedDate = competitor.created_at
    ? new Date(competitor.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'N/A'

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={competitor.company_name}
      subtitle="Competitor Intelligence Profile"
      icon={Building2}
      maxWidth="max-w-xl"
    >
      <div className="space-y-6">
        {/* Main Header Info & Status */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-md">
              {competitor.company_name ? competitor.company_name.substring(0, 2).toUpperCase() : 'CO'}
            </div>
            <div>
              <h4 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {competitor.company_name}
              </h4>
              <a
                href={competitor.website}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-primary-600 dark:text-primary-400 hover:underline mt-0.5"
              >
                <Globe className="w-3.5 h-3.5 mr-1" />
                {competitor.website}
                <ExternalLink className="w-3 h-3 ml-1 opacity-70" />
              </a>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                competitor.is_active !== false
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800/40'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400 border border-gray-200 dark:border-gray-700'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                competitor.is_active !== false ? 'bg-green-500' : 'bg-gray-400'
              }`} />
              {competitor.is_active !== false ? 'Active Monitoring' : 'Inactive'}
            </span>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-3.5 rounded-lg bg-white dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700/70 space-y-1">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center">
              <Tag className="w-3.5 h-3.5 mr-1.5 text-primary-500" />
              Industry
            </span>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {competitor.industry || 'Not specified'}
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-white dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700/70 space-y-1">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center">
              <Flag className="w-3.5 h-3.5 mr-1.5 text-indigo-500" />
              Country
            </span>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {competitor.country || 'Not specified'}
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-white dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700/70 space-y-1">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center">
              <Calendar className="w-3.5 h-3.5 mr-1.5 text-emerald-500" />
              Date Added
            </span>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {formattedDate}
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-white dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700/70 space-y-1">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center">
              <Activity className="w-3.5 h-3.5 mr-1.5 text-purple-500" />
              Last Monitored
            </span>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Recently
            </p>
          </div>
        </div>

        {/* Description Section */}
        {competitor.description && (
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/20 border border-gray-100 dark:border-gray-700/50 space-y-1">
            <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Notes & Description
            </h5>
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
              {competitor.description}
            </p>
          </div>
        )}

        {/* Quick Actions Footer */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-gray-100 dark:border-gray-700/60">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              icon={Edit}
              onClick={() => {
                onClose()
                onEdit?.(competitor)
              }}
            >
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={FileText}
              onClick={() => {
                onClose()
                onGenerateReport?.(competitor)
              }}
            >
              Report
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              onClick={() => {
                onClose()
                onMonitorNow?.(competitor)
              }}
            >
              Monitor
            </Button>
          </div>

          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  )
}
