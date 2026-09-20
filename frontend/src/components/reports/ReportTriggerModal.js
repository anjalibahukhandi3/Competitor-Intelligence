'use client'

import { useState, useEffect } from 'react'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import { FileText, Building2, Sparkles } from 'lucide-react'
import { competitorsApi, reportsApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function ReportTriggerModal({
  isOpen,
  onClose,
  initialCompetitorId = null,
  onSuccess,
}) {
  const [competitors, setCompetitors] = useState([])
  const [selectedCompetitorId, setSelectedCompetitorId] = useState('')
  const [loadingCompetitors, setLoadingCompetitors] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!isOpen) return

    const loadCompetitors = async () => {
      setLoadingCompetitors(true)
      try {
        const res = await competitorsApi.getAll(1, 100)
        const items = res.data?.items || (Array.isArray(res.data) ? res.data : [])
        setCompetitors(items)
        if (initialCompetitorId) {
          setSelectedCompetitorId(initialCompetitorId)
        } else if (items.length > 0) {
          setSelectedCompetitorId(items[0].id)
        }
      } catch (err) {
        console.error('Failed to load competitors for report modal:', err)
        toast.error('Failed to load competitors list')
      } finally {
        setLoadingCompetitors(false)
      }
    }

    loadCompetitors()
  }, [isOpen, initialCompetitorId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedCompetitorId) {
      toast.error('Please select a competitor to analyze')
      return
    }

    setSubmitting(true)
    try {
      await reportsApi.triggerReport(selectedCompetitorId)
      const comp = competitors.find((c) => c.id === selectedCompetitorId)
      toast.success(
        `AI Intelligence Report enqueued for ${comp?.company_name || 'competitor'}!`
      )
      onSuccess?.()
      onClose()
    } catch (err) {
      console.error('Error triggering report:', err)
      toast.error(
        err.response?.data?.detail || 'Failed to trigger report generation'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Generate AI Intelligence Report"
      subtitle="Run automated deep-dive analysis on a competitor"
      icon={Sparkles}
      maxWidth="max-w-md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Select Target Competitor <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
              <Building2 className="w-4 h-4" />
            </div>
            <select
              value={selectedCompetitorId}
              onChange={(e) => setSelectedCompetitorId(e.target.value)}
              disabled={loadingCompetitors || submitting}
              className="input-field pl-10 bg-white dark:bg-gray-800 text-sm"
            >
              {loadingCompetitors ? (
                <option value="">Loading competitors...</option>
              ) : competitors.length === 0 ? (
                <option value="">No competitors found. Add one first.</option>
              ) : (
                competitors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.company_name} ({c.website})
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-800/40 text-xs text-purple-800 dark:text-purple-300 space-y-1">
          <div className="font-semibold flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            AI Report Pipeline
          </div>
          <p className="leading-relaxed opacity-90">
            Triggers web snapshot analysis, SWOT matrix generation, positioning update detection, and strategic threat evaluation.
          </p>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-100 dark:border-gray-700/60 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={submitting}
            disabled={loadingCompetitors || competitors.length === 0}
            icon={FileText}
          >
            Generate Report
          </Button>
        </div>
      </form>
    </Modal>
  )
}
