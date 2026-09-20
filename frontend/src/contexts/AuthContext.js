'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { authApi, clearTokens, getAccessToken } from '@/services/api'
import { isTokenExpired, parseJWT } from '@/utils/helpers'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
  // isAuthenticated is the source of truth — not a user object.
  // The backend login endpoint returns only { access_token, token_type }.
  // There is no /me endpoint and no user object in the login response.
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  // Derive a lightweight display object from the JWT payload so the UI
  // has *something* to show without needing a separate /me API call.
  const [tokenPayload, setTokenPayload] = useState(null)

  const hydrateFromToken = useCallback((token) => {
    if (!token) {
      setIsAuthenticated(false)
      setTokenPayload(null)
      return
    }
    const payload = parseJWT(token) // returns null on any error
    setIsAuthenticated(true)
    setTokenPayload(payload) // { sub: email, exp: ... }
  }, [])

  // ── On mount: read token from localStorage / cookie ──────────────────────
  useEffect(() => {
    try {
      const token = getAccessToken()
      if (token && !isTokenExpired(token)) {
        hydrateFromToken(token)
      } else {
        // Token missing or expired — clear stale data and stay logged out
        clearTokens()
        setIsAuthenticated(false)
        setTokenPayload(null)
      }
    } catch (err) {
      console.error('Auth init error:', err)
      setIsAuthenticated(false)
      setTokenPayload(null)
    } finally {
      setLoading(false)
    }
  }, [hydrateFromToken])

  // ── login ─────────────────────────────────────────────────────────────────
  const login = async (credentials) => {
    try {
      // authApi.login stores the token and returns { access_token, token_type }
      const data = await authApi.login(credentials)
      hydrateFromToken(data.access_token)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      }
    }
  }

  // ── register ──────────────────────────────────────────────────────────────
  const register = async (userData) => {
    try {
      const data = await authApi.register(userData)
      return { success: true, data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      }
    }
  }

  // ── logout ────────────────────────────────────────────────────────────────
  const logout = () => {
    clearTokens()
    setIsAuthenticated(false)
    setTokenPayload(null)
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login'
    }
  }

  // ── Expose a safe "user" shape so existing JSX like user?.email still works.
  // We derive email from the JWT `sub` claim (FastAPI sets sub=email by default).
  const user = isAuthenticated && tokenPayload
    ? {
        email: tokenPayload.sub ?? null,
        // first_name / last_name are not in the token — keep as null
        first_name: null,
        last_name: null,
      }
    : null

  const value = {
    user,           // safe object or null — never crashes on .email etc.
    isAuthenticated,
    loading,
    login,
    register,
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
