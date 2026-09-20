'use client'

import { useState, useEffect } from 'react'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import { Building2, Globe, Tag, Flag, AlignLeft } from 'lucide-react'
import { competitorsApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function CompetitorModal({
  isOpen,
  onClose,
  competitor = null,
  onSuccess,
}) {
  const isEditing = Boolean(competitor?.id)

  const [formData, setFormData] = useState({
    company_name: '',
    website: '',
    industry: '',
    country: '',
    description: '',
  })

  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  // Populate form data when competitor changes or modal opens
  useEffect(() => {
    if (competitor) {
      setFormData({
        company_name: competitor.company_name || '',
        website: competitor.website || '',
        industry: competitor.industry || '',
        country: competitor.country || '',
        description: competitor.description || '',
      })
    } else {
      setFormData({
        company_name: '',
        website: '',
        industry: '',
        country: '',
        description: '',
      })
    }
    setErrors({})
  }, [competitor, isOpen])

  const validate = () => {
    const errs = {}
    if (!formData.company_name.trim()) {
      errs.company_name = 'Company name is required'
    } else if (formData.company_name.trim().length < 2) {
      errs.company_name = 'Company name must be at least 2 characters'
    }

    if (!formData.website.trim()) {
      errs.website = 'Website URL is required'
    } else {
      let rawUrl = formData.website.trim()
      if (!/^https?:\/\//i.test(rawUrl)) {
        rawUrl = 'https://' + rawUrl
      }
      try {
        new URL(rawUrl)
      } catch {
        errs.website = 'Please enter a valid website URL'
      }
    }

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setLoading(true)

    // Format website URL to ensure valid protocol
    let formattedWebsite = formData.website.trim()
    if (!/^https?:\/\//i.test(formattedWebsite)) {
      formattedWebsite = `https://${formattedWebsite}`
    }

    const payload = {
      company_name: formData.company_name.trim(),
      website: formattedWebsite,
      industry: formData.industry.trim() || null,
      country: formData.country.trim() || null,
      description: formData.description.trim() || null,
    }

    try {
      if (isEditing) {
        await competitorsApi.update(competitor.id, payload)
        toast.success(`'${payload.company_name}' updated successfully!`)
      } else {
        await competitorsApi.create(payload)
        toast.success(`'${payload.company_name}' added to tracking!`)
      }

      onSuccess?.()
      onClose()
    } catch (err) {
      console.error('Error saving competitor:', err)
      const message =
        err.response?.data?.detail ||
        (Array.isArray(err.response?.data?.detail)
          ? err.response.data.detail[0]?.msg
          : null) ||
        'Failed to save competitor. Please try again.'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Competitor' : 'Add New Competitor'}
      subtitle={
        isEditing
          ? 'Update the profile details of this competitor'
          : 'Track a new market competitor to monitor their updates'
      }
      icon={Building2}
      maxWidth="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Company Name * */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Company Name <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
              <Building2 className="w-4 h-4" />
            </div>
            <input
              type="text"
              name="company_name"
              placeholder="e.g. Acme Corp"
              value={formData.company_name}
              onChange={handleChange}
              disabled={loading}
              className={`input-field pl-10 ${
                errors.company_name
                  ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500'
                  : ''
              }`}
            />
          </div>
          {errors.company_name && (
            <p className="text-xs text-red-500 mt-1">{errors.company_name}</p>
          )}
        </div>

        {/* Website URL * */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Website URL <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
              <Globe className="w-4 h-4" />
            </div>
            <input
              type="text"
              name="website"
              placeholder="e.g. https://acme.com or acme.com"
              value={formData.website}
              onChange={handleChange}
              disabled={loading}
              className={`input-field pl-10 ${
                errors.website
                  ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500'
                  : ''
              }`}
            />
          </div>
          {errors.website && (
            <p className="text-xs text-red-500 mt-1">{errors.website}</p>
          )}
        </div>

        {/* Grid for Industry & Country */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Industry */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Industry
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                <Tag className="w-4 h-4" />
              </div>
              <input
                type="text"
                name="industry"
                placeholder="e.g. SaaS, E-commerce"
                value={formData.industry}
                onChange={handleChange}
                disabled={loading}
                className="input-field pl-10"
              />
            </div>
          </div>

          {/* Country */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Country
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                <Flag className="w-4 h-4" />
              </div>
              <input
                type="text"
                name="country"
                placeholder="e.g. United States"
                value={formData.country}
                onChange={handleChange}
                disabled={loading}
                className="input-field pl-10"
              />
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Description
          </label>
          <div className="relative">
            <div className="absolute top-3 left-3 flex items-start pointer-events-none text-gray-400">
              <AlignLeft className="w-4 h-4" />
            </div>
            <textarea
              name="description"
              rows={3}
              placeholder="Brief overview or notes about this competitor..."
              value={formData.description}
              onChange={handleChange}
              disabled={loading}
              className="input-field pl-10 py-2 resize-none text-sm"
            />
          </div>
        </div>

        {/* Footer Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-100 dark:border-gray-700/60 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            {isEditing ? 'Save Changes' : 'Save Competitor'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
