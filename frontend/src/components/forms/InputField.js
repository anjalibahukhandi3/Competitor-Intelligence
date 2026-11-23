'use client'

import { forwardRef, useId } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

const InputField = forwardRef(({
  label,
  type = 'text',
  error,
  icon: Icon,
  className = '',
  id,
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = useState(false)
  const generatedId = useId()
  const inputId = id || generatedId
  const inputType = type === 'password' && showPassword ? 'text' : type

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`space-y-2 ${className}`}
    >
      {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Icon className="w-5 h-5 text-gray-400" />
          </div>
        )}
        
        <input
          ref={ref}
          id={inputId}
          type={inputType}
          aria-invalid={Boolean(error)}
          className={`
            input-field
            ${Icon ? 'pl-10' : ''}
            ${type === 'password' ? 'pr-10' : ''}
            ${error ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500' : ''}
          `}
          {...props}
        />
        
        {type === 'password' && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        )}
      </div>
      
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-red-600 dark:text-red-400"
        >
          {error}
        </motion.p>
      )}
    </motion.div>
  )
})

InputField.displayName = 'InputField'

export default InputField
