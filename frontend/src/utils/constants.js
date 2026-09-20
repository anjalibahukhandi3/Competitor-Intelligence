export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'
export const APP_NAME =
  process.env.NEXT_PUBLIC_APP_NAME || 'Competitor Intelligence'
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'

export const ROUTES = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  FORGOT_PASSWORD: '/auth/forgot-password',
  DASHBOARD: '/dashboard',
  COMPETITORS: '/competitors',
  REPORTS: '/reports',
  MONITORING: '/monitoring',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
}

// Exact backend paths — keep in sync with src/api/router.py
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    // No /refresh or /logout — backend does not implement them
  },
  COMPETITORS: {
    LIST: '/competitors/',
    CREATE: '/competitors/',
    DETAIL: (id) => `/competitors/${id}`,
    UPDATE: (id) => `/competitors/${id}`,   // PATCH
    DELETE: (id) => `/competitors/${id}`,
    TIMELINE: (id) => `/competitors/${id}/timeline`,
  },
  REPORTS: {
    TRIGGER: (competitorId) => `/reports/trigger/${competitorId}`,
    DETAIL: (reportId) => `/reports/${reportId}`,
    LIST: (competitorId) => `/reports/${competitorId}/list`,
    DOWNLOAD: (reportId) => `/reports/${reportId}/download`,
  },
  MONITORING: {
    RUN: '/monitor/run',
    CHANGES: '/changes',
    SNAPSHOT: (id) => `/snapshots/${id}`,
    FREQUENCY: (id) => `/monitoring/${id}/frequency`,
    TRIGGER: (id) => `/monitoring/${id}/trigger`,
  },
}

// localStorage / cookie keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  // No REFRESH_TOKEN — backend has no refresh endpoint
  THEME: 'theme',
}

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
}
