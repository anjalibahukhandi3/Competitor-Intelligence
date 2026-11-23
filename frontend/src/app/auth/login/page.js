'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { ArrowRight, LockKeyhole, Mail, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'
import { APP_NAME } from '@/utils/constants'
import Button from '@/components/ui/Button'
import InputField from '@/components/forms/InputField'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = async (data) => {
    setIsLoading(true)

    try {
      const result = await login(data)

      if (result.success) {
        toast.success('Welcome back!')
        router.push('/dashboard')
      } else {
        toast.error(result.error || 'Login failed')
      }
    } catch (error) {
      toast.error('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.38, ease: 'easeOut' }}
      className="login-panel w-full"
    >
      <div className="mb-7 text-center sm:mb-8">
        <span className="login-icon mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-[1.2rem]">
          <Sparkles className="h-6 w-6" strokeWidth={1.8} />
        </span>
        <p className="mb-2 text-[11px] font-bold uppercase tracking-[.17em] text-violet-700">Your market, in focus</p>
        <h1 className="text-3xl font-semibold tracking-[-.055em] text-slate-950">Welcome back</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">Sign in to continue to your {APP_NAME} workspace.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <InputField
          label="Email address"
          type="email"
          icon={Mail}
          autoComplete="email"
          placeholder="you@company.com"
          error={errors.email?.message}
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Enter a valid email address',
            },
          })}
        />

        <InputField
          label="Password"
          type="password"
          icon={LockKeyhole}
          autoComplete="current-password"
          placeholder="Enter your password"
          error={errors.password?.message}
          {...register('password', {
            required: 'Password is required',
            minLength: {
              value: 6,
              message: 'Password must be at least 6 characters',
            },
          })}
        />

        <div className="flex justify-end pt-0.5">
          <Link href="/auth/forgot-password" className="text-sm font-semibold text-violet-700 transition hover:text-violet-900 hover:underline">
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          loading={isLoading}
          className="login-submit w-full"
          size="lg"
          icon={ArrowRight}
          iconPosition="right"
        >
          Sign in
        </Button>
      </form>

      <div className="my-6 flex items-center gap-3 text-[11px] font-medium text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />
        NEW TO THE WORKSPACE?
        <span className="h-px flex-1 bg-slate-200" />
      </div>

      <Link href="/auth/register" className="login-create-link flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 transition">
        Create an account
      </Link>

      <p className="mt-6 text-center text-xs leading-5 text-slate-500">
        Your workspace brings competitor monitoring and research together.
      </p>
    </motion.section>
  )
}
