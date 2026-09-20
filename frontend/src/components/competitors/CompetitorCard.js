'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe,
  Tag,
  Flag,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  FileText,
  RefreshCw,
  ExternalLink,
  Calendar,
} from 'lucide-react'
import Card from '@/components/ui/Card'

export default function CompetitorCard({
  competitor,
  onView,
  onEdit,
  onDelete,
  onGenerateReport,
  onMonitorNow,
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  // Close dropdown menu when clicking outside
  useEffect(() => {
    if (!menuOpen) return
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [menuOpen])

  const formattedDate = competitor.created_at
    ? new Date(competitor.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Recently'

  // Extract initial for avatar
  const avatarLetter = competitor.company_name
    ? competitor.company_name.charAt(0).toUpperCase()
    : 'C'

  return (
    <Card className="p-5 flex flex-col justify-between relative group hover:shadow-xl transition-all duration-300">
      {/* Top Header Row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center space-x-3 min-w-0">
          {/* Avatar Icon */}
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-500 text-white font-bold text-lg flex items-center justify-center flex-shrink-0 shadow-md group-hover:scale-105 transition-transform">
            {avatarLetter}
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
              {competitor.company_name}
            </h3>
            <a
              href={competitor.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-xs text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 truncate max-w-full transition-colors mt-0.5"
              title={competitor.website}
            >
              <Globe className="w-3 h-3 mr-1 flex-shrink-0" />
              <span className="truncate">{competitor.website.replace(/^https?:\/\//, '')}</span>
              <ExternalLink className="w-2.5 h-2.5 ml-1 flex-shrink-0 opacity-60" />
            </a>
          </div>
        </div>

        {/* Action Menu (3-dots) Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            type="button"
            className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors focus:outline-none"
            aria-label="Actions menu"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -5 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -5 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-100 dark:border-gray-700 py-1 z-30 overflow-hidden text-sm"
              >
                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onView?.(competitor)
                  }}
                  className="w-full flex items-center px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <Eye className="w-4 h-4 mr-2.5 text-gray-500 dark:text-gray-400" />
                  View
                </button>

                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onEdit?.(competitor)
                  }}
                  className="w-full flex items-center px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <Edit className="w-4 h-4 mr-2.5 text-blue-500" />
                  Edit
                </button>

                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onGenerateReport?.(competitor)
                  }}
                  className="w-full flex items-center px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <FileText className="w-4 h-4 mr-2.5 text-purple-500" />
                  Generate Report
                </button>

                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onMonitorNow?.(competitor)
                  }}
                  className="w-full flex items-center px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <RefreshCw className="w-4 h-4 mr-2.5 text-emerald-500" />
                  Monitor Now
                </button>

                <div className="border-t border-gray-100 dark:border-gray-700/60 my-1" />

                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onDelete?.(competitor)
                  }}
                  className="w-full flex items-center px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <Trash2 className="w-4 h-4 mr-2.5" />
                  Delete
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Description Snippet if present */}
      {competitor.description && (
        <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 my-2 leading-relaxed">
          {competitor.description}
        </p>
      )}

      {/* Tags / Details Row */}
      <div className="flex flex-wrap items-center gap-2 my-3">
        {competitor.industry && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800/40">
            <Tag className="w-3 h-3 mr-1 opacity-70" />
            {competitor.industry}
          </span>
        )}

        {competitor.country && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700/50 dark:text-gray-300">
            <Flag className="w-3 h-3 mr-1 opacity-70" />
            {competitor.country}
          </span>
        )}

        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ml-auto ${
            competitor.is_active !== false
              ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200/60 dark:border-green-800/40'
              : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
              competitor.is_active !== false ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
            }`}
          />
          {competitor.is_active !== false ? 'Active' : 'Inactive'}
        </span>
      </div>

      {/* Card Footer: Metadata */}
      <div className="pt-3 mt-1 border-t border-gray-100 dark:border-gray-700/60 flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
        <div className="flex items-center space-x-1">
          <Calendar className="w-3 h-3" />
          <span>Added {formattedDate}</span>
        </div>
        <span>Monitored</span>
      </div>
    </Card>
  )
}
