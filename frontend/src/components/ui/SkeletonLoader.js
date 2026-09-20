'use client'

import { motion } from 'framer-motion'

export default function SkeletonLoader({ className = '', variant = 'rectangular' }) {
  const variants = {
    text: 'h-4 rounded',
    rectangular: 'h-32 rounded-lg',
    circular: 'rounded-full aspect-square',
    card: 'h-48 rounded-xl'
  }

  return (
    <motion.div
      className={`bg-gray-200 dark:bg-gray-700 animate-pulse ${variants[variant]} ${className}`}
      initial={{ opacity: 0.6 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1, repeat: Infinity, repeatType: 'reverse' }}
    />
  )
}