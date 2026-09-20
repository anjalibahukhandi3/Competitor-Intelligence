'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { Mail, Lock, User, Building, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'
import { APP_NAME } from '@/utils/constants'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import InputField from '@/components/forms/InputField'

export default function RegisterPage() {
  const router = useRouter()
  const { register: authRegister } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      company: '',
      password: '',
      confirmPassword: ''
    }
  })

  const password = watch('password')

  const onSubmit = async (data) => {
    setIsLoading(true)
    
    try {
      // Remove confirmPassword from the data sent to API
      const { confirmPassword, ...registerData } = data
      
      const result = await authRegister(registerData)
      
      if (result.success) {
        toast.success('Account created successfully! Please sign in.')
        router.push('/auth/login')
      } else {
        toast.error(result.error || 'Registration failed')
      }
    } catch (error) {
      toast.error('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
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
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
            className="w-16 h-16 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl flex items-center justify-center mx-auto mb-4"
          >
            <Zap className="w-8 h-8 text-white" />
          </motion.div>
          
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2"
          >
            Create your account
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-gray-600 dark:text-gray-400"
          >
            Join {APP_NAME} and start monitoring your competitors
          </motion.p>
        </div>

        {/* Registration Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InputField
              label="First Name"
              type="text"
              icon={User}
              placeholder="John"
              error={errors.first_name?.message}
              {...register('first_name', {
                required: 'First name is required',
                minLength: {
                  value: 2,
                  message: 'First name must be at least 2 characters'
                }
              })}
            />

            <InputField
              label="Last Name"
              type="text"
              icon={User}
              placeholder="Doe"
              error={errors.last_name?.message}
              {...register('last_name', {
                required: 'Last name is required',
                minLength: {
                  value: 2,
                  message: 'Last name must be at least 2 characters'
                }
              })}
            />
          </div>

          <InputField
            label="Email Address"
            type="email"
            icon={Mail}
            placeholder="john@company.com"
            error={errors.email?.message}
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address'
              }
            })}
          />

          <InputField
            label="Company (Optional)"
            type="text"
            icon={Building}
            placeholder="Your company name"
            error={errors.company?.message}
            {...register('company')}
          />

          <InputField
            label="Password"
            type="password"
            icon={Lock}
            placeholder="Create a secure password"
            error={errors.password?.message}
            {...register('password', {
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters'
              },
              pattern: {
                value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                message: 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
              }
            })}
          />

          <InputField
            label="Confirm Password"
            type="password"
            icon={Lock}
            placeholder="Confirm your password"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword', {
              required: 'Please confirm your password',
              validate: (value) =>
                value === password || 'Passwords do not match'
            })}
          />

          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              className="w-4 h-4 mt-1 text-primary-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-primary-500 focus:ring-2"
              {...register('acceptTerms', {
                required: 'You must accept the terms and conditions'
              })}
            />
            <div className="text-sm">
              <label className="text-gray-600 dark:text-gray-400">
                I agree to the{' '}
                <Link href="/terms" className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium">
                  Terms of Service
                </Link>
                {' '}and{' '}
                <Link href="/privacy" className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium">
                  Privacy Policy
                </Link>
              </label>
              {errors.acceptTerms && (
                <p className="text-red-600 dark:text-red-400 mt-1">
                  {errors.acceptTerms.message}
                </p>
              )}
            </div>
          </div>

          <Button
            type="submit"
            loading={isLoading}
            className="w-full"
            size="lg"
          >
            Create Account
          </Button>
        </form>

        {/* Divider */}
        <div className="my-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200 dark:border-gray-700" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                Already have an account?
              </span>
            </div>
          </div>
        </div>

        {/* Sign In Link */}
        <div className="text-center">
          <Link href="/auth/login">
            <Button variant="outline" className="w-full">
              Sign In Instead
            </Button>
          </Link>
        </div>
      </Card>

      {/* Security Note */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
      >
        <h4 className="text-sm font-medium text-green-900 dark:text-green-200 mb-2">
          🔒 Your data is secure
        </h4>
        <p className="text-xs text-green-700 dark:text-green-300">
          We use industry-standard encryption to protect your information and never share your data with third parties.
        </p>
      </motion.div>
    </motion.div>
  )
}