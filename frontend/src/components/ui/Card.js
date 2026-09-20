'use client'

import { motion } from 'framer-motion'

export default function Card({ 
  children, 
  className = '', 
  hover = true, 
  glass = false,
  ...props 
}) {
  const baseClasses = glass ? 'glass' : 'card'
  const hoverClasses = hover ? 'hover:shadow-xl hover:-translate-y-1' : ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${baseClasses} ${hoverClasses} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  )
}