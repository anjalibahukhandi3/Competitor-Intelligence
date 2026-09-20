'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
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

  const changeIcon = changeType === 'positive' ? TrendingUp : TrendingDown
  const changeColor = changeType === 'positive' 
    ? 'text-green-600 dark:text-green-400' 
    : 'text-red-600 dark:text-red-400'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card className="p-6 relative overflow-hidden">
        {/* Background Gradient */}
        <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${colorClasses[color]} opacity-10 rounded-full transform translate-x-8 -translate-y-8`} />
        
        <div className="relative">
          {/* Icon */}
          <div className={`w-12 h-12 bg-gradient-to-r ${colorClasses[color]} rounded-lg flex items-center justify-center mb-4`}>
            <Icon className="w-6 h-6 text-white" />
          </div>

          {/* Content */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {label}
            </p>
            
            <div className="flex items-end justify-between">
              <motion.p
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: delay + 0.2 }}
                className="text-3xl font-bold text-gray-900 dark:text-gray-100"
              >
                {value}
              </motion.p>
              
              {change && (
                <motion.div
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: delay + 0.3 }}
                  className={`flex items-center text-sm font-medium ${changeColor}`}
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