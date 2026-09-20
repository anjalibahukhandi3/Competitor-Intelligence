'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { STORAGE_KEYS, THEMES } from '@/utils/constants'

const ThemeContext = createContext({})

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(THEMES.SYSTEM)
  const [resolvedTheme, setResolvedTheme] = useState(THEMES.LIGHT)

  useEffect(() => {
    // Load theme from localStorage
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || THEMES.SYSTEM
      setTheme(savedTheme)
      updateResolvedTheme(savedTheme)
    }
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      
      const handleChange = () => {
        if (theme === THEMES.SYSTEM) {
          updateResolvedTheme(THEMES.SYSTEM)
        }
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  const updateResolvedTheme = (currentTheme) => {
    let resolved = currentTheme

    if (currentTheme === THEMES.SYSTEM && typeof window !== 'undefined') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? THEMES.DARK
        : THEMES.LIGHT
    }

    setResolvedTheme(resolved)

    // Update DOM
    if (typeof document !== 'undefined') {
      const root = document.documentElement
      root.classList.remove(THEMES.LIGHT, THEMES.DARK)
      root.classList.add(resolved)
    }
  }

  const changeTheme = (newTheme) => {
    setTheme(newTheme)
    updateResolvedTheme(newTheme)
    
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.THEME, newTheme)
    }
  }

  const value = {
    theme,
    resolvedTheme,
    changeTheme,
    isDark: resolvedTheme === THEMES.DARK
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}