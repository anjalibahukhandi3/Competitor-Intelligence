'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Plus,
  FileText,
  Settings,
  Search,
  Bell,
  BarChart3,
  Users,
  Activity,
} from 'lucide-react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import CompetitorModal from '@/components/competitors/CompetitorModal'
import ReportTriggerModal from '@/components/reports/ReportTriggerModal'

const quickActions = [
  {
    id: 1,
    title: 'Add Competitor',
    description: 'Start monitoring a new competitor',
    icon: Plus,
    color: 'blue',
    action: 'add-competitor',
  },
  {
    id: 2,
    title: 'Generate Report',
    description: 'Create a new AI analysis report',
    icon: FileText,
    color: 'purple',
    action: 'generate-report',
  },
  {
    id: 3,
    title: 'View Analytics',
    description: 'Check detailed analytics & trends',
    icon: BarChart3,
    color: 'green',
    action: 'view-analytics',
  },
  {
    id: 4,
    title: 'Search Insights',
    description: 'Find specific competitor data',
    icon: Search,
    color: 'orange',
    action: 'search-insights',
  },
]

const monitoringActions = [
  {
    id: 1,
    title: 'Setup Alerts',
    description: 'Configure monitoring alerts',
    icon: Bell,
    color: 'red',
    href: '/settings',
  },
  {
    id: 2,
    title: 'Manage Competitors',
    description: 'Edit competitor settings',
    icon: Users,
    color: 'blue',
    href: '/competitors',
  },
  {
    id: 3,
    title: 'Monitor Activity',
    description: 'View real-time changes',
    icon: Activity,
    color: 'green',
    href: '/monitoring',
  },
  {
    id: 4,
    title: 'Settings',
    description: 'Update preferences',
    icon: Settings,
    color: 'gray',
    href: '/settings',
  },
]

export default function QuickActions() {
  const router = useRouter()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isReportModalOpen, setIsReportModalOpen] = useState(false)

  const getColorClasses = (color) => {
    const colors = {
      blue: 'from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700',
      purple: 'from-violet-500 to-violet-600 hover:from-violet-600 hover:to-violet-700',
      green: 'from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700',
      orange: 'from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700',
      red: 'from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700',
      gray: 'from-stone-500 to-stone-600 hover:from-stone-600 hover:to-stone-700',
    }
    return colors[color] || colors.blue
  }

  const handleAction = (actionType) => {
    if (actionType === 'add-competitor') {
      setIsAddModalOpen(true)
    } else if (actionType === 'generate-report') {
      setIsReportModalOpen(true)
    } else if (actionType === 'view-analytics') {
      router.push('/analytics')
    } else if (actionType === 'search-insights') {
      router.push('/competitors')
    }
  }

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-r from-teal-500 to-amber-500 rounded-lg flex items-center justify-center">
          <Settings className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Quick Actions
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Frequently used features
          </p>
        </div>
      </div>

      {/* Primary Actions */}
      <div className="space-y-3 mb-6">
        {quickActions.map((action, index) => {
          const Icon = action.icon

          return (
            <motion.button
              key={action.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => handleAction(action.action)}
              className={`w-full p-4 bg-gradient-to-r ${getColorClasses(
                action.color
              )} rounded-lg text-white text-left transition-all duration-200 hover:scale-105 hover:shadow-lg group`}
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-5 h-5 group-hover:scale-110 transition-transform" />
                <div>
                  <h4 className="font-medium text-sm">{action.title}</h4>
                  <p className="text-xs opacity-90">{action.description}</p>
                </div>
              </div>
            </motion.button>
          )
        })}
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">
          Monitoring Tools
        </h4>

        {/* Secondary Actions Grid */}
        <div className="grid grid-cols-2 gap-3">
          {monitoringActions.map((action, index) => {
            const Icon = action.icon

            return (
              <motion.button
                key={action.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                onClick={() => router.push(action.href)}
                className="p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-all duration-200 hover:scale-105 group text-left"
              >
                <div className="flex flex-col items-center text-center space-y-2">
                  <div
                    className={`w-8 h-8 bg-gradient-to-r ${getColorClasses(
                      action.color
                    )} rounded-lg flex items-center justify-center`}
                  >
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-900 dark:text-gray-100">
                      {action.title}
                    </h5>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                      {action.description}
                    </p>
                  </div>
                </div>
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* Modals */}
      <CompetitorModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => router.push('/competitors')}
      />

      <ReportTriggerModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onSuccess={() => router.push('/reports')}
      />
    </Card>
  )
}