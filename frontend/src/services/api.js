import axios from 'axios'
import Cookies from 'js-cookie'
import toast from 'react-hot-toast'
import { API_BASE_URL, STORAGE_KEYS } from '@/utils/constants'
import { isTokenExpired } from '@/utils/helpers'

// ─────────────────────────────────────────────
// Axios Instance
// ─────────────────────────────────────────────

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─────────────────────────────────────────────
// Token Helpers  (access token only — backend has no refresh endpoint)
// ─────────────────────────────────────────────

export const getAccessToken = () => {
  if (typeof window === 'undefined') return null
  return (
    localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) ||
    Cookies.get(STORAGE_KEYS.ACCESS_TOKEN) ||
    null
  )
}

const setAccessToken = (token) => {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token)
  // Also write to cookie so middleware can read it server-side
  Cookies.set(STORAGE_KEYS.ACCESS_TOKEN, token, { expires: 1 })
}

export const clearTokens = () => {
  if (typeof window === 'undefined') return
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
  Cookies.remove(STORAGE_KEYS.ACCESS_TOKEN)
}

// ─────────────────────────────────────────────
// Request Interceptor — attach Bearer token
// ─────────────────────────────────────────────

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token && !isTokenExpired(token)) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─────────────────────────────────────────────
// Response Interceptor — handle 401 globally
// ─────────────────────────────────────────────

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearTokens()
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
      return Promise.reject(error)
    }

    // Show toast for all other errors (skip on 401 to avoid flash before redirect)
    if (typeof window !== 'undefined') {
      const message =
        error.response?.data?.detail ||
        error.message ||
        'Something went wrong'
      toast.error(message)
    }

    return Promise.reject(error)
  }
)

// ─────────────────────────────────────────────
// Authentication API
// ─────────────────────────────────────────────

export const authApi = {
  /**
   * POST /auth/login
   * Backend returns: { access_token, token_type }
   * No user object, no refresh token.
   */
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials)
    const { access_token } = response.data
    setAccessToken(access_token)
    return response.data
  },

  /**
   * POST /auth/register
   * Backend returns: UserResponse { id, email, is_active, created_at }
   * Backend UserCreate only accepts: { email, password }
   */
  register: async (userData) => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  logout: () => {
    clearTokens()
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login'
    }
  },
}

// ─────────────────────────────────────────────
// Competitors API
// Trailing slash required — backend routes: POST /competitors/, GET /competitors/
// ─────────────────────────────────────────────

export const competitorsApi = {
  getAll: (page = 1, size = 20) =>
    api.get('/competitors/', { params: { page, size } }),
  getById: (id) => api.get(`/competitors/${id}`),
  create: (data) => api.post('/competitors/', data),
  update: (id, data) => api.patch(`/competitors/${id}`, data), // backend uses PATCH
  delete: (id) => api.delete(`/competitors/${id}`),
}

// ─────────────────────────────────────────────
// Reports API
// Backend routes:
//   POST /reports/trigger/{competitor_id}
//   GET  /reports/{report_id}
//   GET  /reports/{competitor_id}/list
//   GET  /reports/{report_id}/download
// ─────────────────────────────────────────────

export const reportsApi = {
  triggerReport: (competitorId) =>
    api.post(`/reports/trigger/${competitorId}`),
  getById: (reportId) => api.get(`/reports/${reportId}`),
  listForCompetitor: (competitorId, page = 1, size = 20) =>
    api.get(`/reports/${competitorId}/list`, { params: { page, size } }),
  download: (reportId) =>
    api.get(`/reports/${reportId}/download`, { responseType: 'blob' }),
  updateStatus: (reportId, status) =>
    api.patch(`/reports/${reportId}/status`, { status }),
}

// ─────────────────────────────────────────────
// Monitoring API
// Backend routes (monitoring.py):
//   PUT  /monitoring/{competitor_id}/frequency
//   POST /monitoring/{competitor_id}/trigger
// Backend routes (snapshots/routes.py):
//   POST /monitor/run
//   GET  /competitors/{id}/timeline
//   GET  /snapshots/{id}
//   GET  /changes
// ─────────────────────────────────────────────

export const monitoringApi = {
  /** Trigger a manual monitoring run for one or all competitors */
  runMonitoring: (competitorIds = null) =>
    api.post('/monitor/run', { competitor_ids: competitorIds }),

  /** Get the intelligence timeline for a competitor */
  getTimeline: (competitorId, limit = 50) =>
    api.get(`/competitors/${competitorId}/timeline`, { params: { limit } }),

  /** List recent change events across all competitors */
  getChanges: (limit = 50, category = null, impact = null) =>
    api.get('/changes', { params: { limit, category, impact } }),

  /** Get a specific snapshot */
  getSnapshot: (snapshotId) => api.get(`/snapshots/${snapshotId}`),

  /** Update monitoring frequency for a competitor */
  updateFrequency: (competitorId, frequency) =>
    api.put(`/monitoring/${competitorId}/frequency`, null, {
      params: { frequency },
    }),

  /** Trigger manual monitoring for a single competitor */
  triggerForCompetitor: (competitorId) =>
    api.post(`/monitoring/${competitorId}/trigger`),
}

export default api
