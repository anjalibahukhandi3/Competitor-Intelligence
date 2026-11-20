'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { Mail, ArrowLeft } from 'lucide-react'
import { APP_NAME } from '@/utils/constants'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import InputField from '@/components/forms/InputField'

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      email: ''
    }
  })

  const onSubmit = async (data) => {
    setIsLoading(true)
    // Password recovery is not implemented by the backend yet. Do not claim
    // an email was sent when no recovery request can be made.
    setIsLoading(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full"
    >
      <Card className="p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2"
          >
            Reset your password
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-gray-600 dark:text-gray-400"
          >
            Password recovery is not available yet. Contact your administrator to regain access.
          </motion.p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <InputField
            label="Email Address"
            type="email"
            icon={Mail}
            placeholder="Enter your email"
            error={errors.email?.message}
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address'
              }
            })}
          />

          <Button type="button" disabled className="w-full" size="lg">
            Password reset unavailable
          </Button>
        </form>

        {/* Back to Sign In */}
        <div className="mt-6 text-center">
          <Link
            href="/auth/login"
            className="inline-flex items-center space-x-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Sign In</span>
          </Link>
        </div>
      </Card>

      {/* Help */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-6 p-4 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg"
      >
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-200 mb-2">
          Need help?
        </h4>
        <p className="text-xs text-gray-600 dark:text-gray-400">
          Contact our support team if you&apos;re having trouble accessing your account.
        </p>
      </motion.div>
    </motion.div>
  )
}
