'use client'

import { useState, useEffect } from 'react'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { Globe, Hash, Calendar, FileCode } from 'lucide-react'
import { monitoringApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function SnapshotViewModal({ isOpen, onClose, snapshotId }) {
  const [snapshot, setSnapshot] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('homepage')

  useEffect(() => {
    if (!isOpen || !snapshotId) return

    const fetchSnapshot = async () => {
      setLoading(true)
      try {
        const res = await monitoringApi.getSnapshot(snapshotId)
        setSnapshot(res.data)
      } catch (err) {
        console.error('Failed to load snapshot:', err)
        toast.error('Failed to load website snapshot')
      } finally {
        setLoading(false)
      }
    }

    fetchSnapshot()
  }, [isOpen, snapshotId])

  if (!isOpen) return null

  const formattedDate = snapshot?.created_at
    ? new Date(snapshot.created_at).toLocaleString()
    : 'N/A'

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Competitor Website Snapshot"
      subtitle={`Captured Content (ID: ${snapshotId?.substring(0, 8)}...)`}
      icon={Globe}
      maxWidth="max-w-3xl"
    >
      {loading ? (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" />
          <p className="text-sm text-gray-500">Loading website snapshot...</p>
        </div>
      ) : !snapshot ? (
        <div className="py-10 text-center text-gray-500">
          Snapshot content unavailable.
        </div>
      ) : (
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          {/* Metadata banner */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700 text-xs">
            <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-300">
              <Calendar className="w-3.5 h-3.5" />
              <span>Captured: {formattedDate}</span>
            </div>

            {snapshot.content_hash && (
              <div className="flex items-center space-x-1.5 font-mono text-gray-500 dark:text-gray-400">
                <Hash className="w-3 h-3" />
                <span>Hash: {snapshot.content_hash.substring(0, 12)}...</span>
              </div>
            )}
          </div>

          {/* Sub-tabs */}
          <div className="flex items-center space-x-2 border-b border-gray-200 dark:border-gray-700 pb-2">
            <button
              onClick={() => setActiveTab('homepage')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'homepage'
                  ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              Homepage Content
            </button>

            <button
              onClick={() => setActiveTab('pricing')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'pricing'
                  ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              Pricing Content
            </button>
          </div>

          {/* Content Body */}
          <div className="p-4 rounded-xl bg-gray-900 text-gray-100 font-mono text-xs overflow-x-auto leading-relaxed max-h-96">
            {activeTab === 'homepage' ? (
              snapshot.homepage_markdown ? (
                <pre className="whitespace-pre-wrap">{snapshot.homepage_markdown}</pre>
              ) : (
                <p className="text-gray-500 italic">No homepage content captured in this snapshot.</p>
              )
            ) : snapshot.pricing_markdown ? (
              <pre className="whitespace-pre-wrap">{snapshot.pricing_markdown}</pre>
            ) : (
              <p className="text-gray-500 italic">No pricing content captured in this snapshot.</p>
            )}
          </div>

          <div className="flex justify-end pt-2">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
