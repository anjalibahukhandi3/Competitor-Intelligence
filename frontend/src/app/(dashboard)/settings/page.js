'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings, User, Bell, Shield, Palette } from 'lucide-react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import toast from 'react-hot-toast'
import { useTheme } from '@/contexts/ThemeContext'

export default function SettingsPage() {
  const { isDark, changeTheme } = useTheme()

  const [toggles, setToggles] = useState({
    email: true,
    desktop: false,
    autoReports: true,
  })

  const handleToggle = (key) => {
    setToggles((prev) => {
      const next = { ...prev, [key]: !prev[key] }
      toast.success(`Preference updated!`)
      return next
    })
  }

  const handleConfigureSection = (title) => {
    if (title === 'Appearance') {
      changeTheme(isDark ? 'light' : 'dark')
      toast.success(`Switched theme to ${isDark ? 'light' : 'dark'} mode`)
    } else {
      toast.success(`${title} configuration updated`)
    }
  }

  const settingsSections = [
    {
      title: 'Profile Settings',
      description: 'Manage your account information and preferences',
      icon: User,
      color: 'blue',
    },
    {
      title: 'Notifications',
      description: 'Configure alerts and email notifications',
      icon: Bell,
      color: 'orange',
    },
    {
      title: 'Security',
      description: 'Update password and security settings',
      icon: Shield,
      color: 'green',
    },
    {
      title: 'Appearance',
      description: `Current mode: ${isDark ? 'Dark' : 'Light'}. Toggle theme mode`,
      icon: Palette,
      color: 'purple',
    },
  ]

  const getColorClasses = (color) => {
    const colors = {
      blue: 'from-blue-500 to-blue-600',
      orange: 'from-orange-500 to-orange-600',
      green: 'from-green-500 to-green-600',
      purple: 'from-purple-500 to-purple-600',
    }
    return colors[color] || colors.blue
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-7xl mx-auto pb-12"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">
            Manage your account and application preferences
          </p>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {settingsSections.map((section, index) => {
          const Icon = section.icon

          return (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer group">
                <div className="flex items-start space-x-4">
                  <div
                    className={`w-12 h-12 bg-gradient-to-r ${getColorClasses(
                      section.color
                    )} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>

                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                      {section.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 text-xs mb-4">
                      {section.description}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleConfigureSection(section.title)}
                    >
                      {section.title === 'Appearance' ? 'Toggle Theme' : 'Configure'}
                    </Button>
                  </div>
                </div>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Quick Settings */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Quick Settings
        </h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Email Notifications
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Receive email alerts for important updates
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={toggles.email}
                onChange={() => handleToggle('email')}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Desktop Notifications
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Show browser notifications for real-time alerts
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={toggles.desktop}
                onChange={() => handleToggle('desktop')}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Auto-generate Reports
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Automatically create weekly summary reports
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={toggles.autoReports}
                onChange={() => handleToggle('autoReports')}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}