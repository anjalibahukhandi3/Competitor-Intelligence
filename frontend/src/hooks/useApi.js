'use client'

import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'

export function useApi(apiCall) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiCall()
      setData(response.data)
    } catch (err) {
      setError(err)
      console.error('API call failed:', err)
    } finally {
      setLoading(false)
    }
  }, [apiCall])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const refetch = () => {
    fetchData()
  }

  return { data, loading, error, refetch }
}

export function useMutation(mutationFn, options = {}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const mutate = async (variables) => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await mutationFn(variables)
      
      if (options.onSuccess) {
        options.onSuccess(result)
      }
      
      if (options.successMessage) {
        toast.success(options.successMessage)
      }
      
      return { success: true, data: result }
    } catch (err) {
      setError(err)
      
      if (options.onError) {
        options.onError(err)
      }
      
      const errorMessage = err.response?.data?.detail || err.message || 'An error occurred'
      
      if (options.errorMessage !== false) {
        toast.error(options.errorMessage || errorMessage)
      }
      
      return { success: false, error: err }
    } finally {
      setLoading(false)
    }
  }

  return { mutate, loading, error }
}