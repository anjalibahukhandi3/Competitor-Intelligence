'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Sparkles } from 'lucide-react'
import Card from '@/components/ui/Card'

export default function StatsCard({
  label,
  value,
  change,
  changeType = 'positive',
  icon: Icon,
  color = 'blue',
  delay = 0
}) {
  const colorClasses = {
    blue: 'from-teal-500 to-teal-600',
    green: 'from-emerald-500 to-emerald-600',
    purple: 'from-violet-500 to-violet-600',
    orange: 'from-amber-500 to-amber-600'
  }

  const bgColors = {
    blue: 'bg-teal-50 dark:bg-teal-900/20',
    green: 'bg-emerald-50 dark:bg-emerald-900/20',
    purple: 'bg-violet-50 dark:bg-violet-900/20',
    orange: 'bg-amber-50 dark:bg-amber-900/20'
  }

  const changeIcon = changeType === 'positive' ? TrendingUp : TrendingDown
  const changeColor = changeType === 'positive'
    ? 'text-green-600 dark:text-green-400'
    : 'text-red-600 dark:text-red-400'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, duration: 0.5, type: 'spring', stiffness: 100 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
      <Card className="p-6 relative overflow-hidden group">
        <div className={`absolute inset-0 ${bgColors[color]} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
        <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${colorClasses[color]} opacity-10 rounded-full transform translate-x-12 -translate-y-12 group-hover:scale-150 transition-transform duration-500`} />

        <div className="relative">
          <motion.div
            className={`w-12 h-12 bg-gradient-to-r ${colorClasses[color]} rounded-xl flex items-center justify-center mb-4 shadow-lg`}
            whileHover={{ rotate: [0, -10, 10, -10, 0], transition: { duration: 0.5 } }}
          >
            <Icon className="w-6 h-6 text-white" />
            <Sparkles className="w-3 h-3 text-white absolute -top-1 -right-1 animate-pulse" />
          </motion.div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {label}
            </p>

            <div className="flex items-end justify-between">
              <motion.p
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: delay + 0.2, duration: 0.4, type: 'spring' }}
                className="text-3xl font-bold text-gray-900 dark:text-gray-100 tracking-tight"
              >
                {value}
              </motion.p>

              {change && (
                <motion.div
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: delay + 0.3 }}
                  className={`flex items-center text-sm font-medium ${changeColor} bg-white/50 dark:bg-gray-800/50 px-2 py-1 rounded-full`}
                >
                  {React.createElement(changeIcon, { className: 'w-4 h-4 mr-1' })}
                  {change}
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}