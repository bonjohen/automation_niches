'use client'

import { use, useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { entitiesApi, Entity } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Input, Card, CardHeader } from '@/components/ui'
import { ArrowLeft, Loader2, AlertCircle, Save } from 'lucide-react'

interface EditVendorPageProps {
  params: Promise<{ id: string }>
}

const vendorTypes = [
  'General Contractor',
  'Subcontractor',
  'Supplier',
  'Service Provider',
  'Consultant',
  'Property Management',
  'Maintenance',
  'Other',
]

const riskLevels = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

const workLocationOptions = [
  'On-site',
  'Remote',
  'Client locations',
  'Multiple sites',
]

interface FormData {
  name: string
  description: string
  email: string
  phone: string
  address: string
  status: string
  vendor_type: string
  contact_name: string
  contact_email: string
  contact_phone: string
  tax_id: string
  contract_start_date: string
  contract_end_date: string
  annual_contract_value: string
  risk_level: string
  services_provided: string
  work_locations: string[]
  requires_auto_coverage: boolean
  requires_workers_comp: boolean
  notes: string
}

export default function EditVendorPage({ params }: EditVendorPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    email: '',
    phone: '',
    address: '',
    status: 'active',
    vendor_type: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    tax_id: '',
    contract_start_date: '',
    contract_end_date: '',
    annual_contract_value: '',
    risk_level: 'medium',
    services_provided: '',
    work_locations: [],
    requires_auto_coverage: false,
    requires_workers_comp: true,
    notes: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const {
    data: vendor,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['entity', id],
    queryFn: () => entitiesApi.get(id),
  })

  // Populate form when vendor data is loaded
  useEffect(() => {
    if (vendor) {
      const cf = vendor.custom_fields || {}
      setFormData({
        name: vendor.name || '',
        description: vendor.description || '',
        email: vendor.email || '',
        phone: vendor.phone || '',
        address: vendor.address || '',
        status: vendor.status || 'active',
        vendor_type: (cf.vendor_type as string) || '',
        contact_name: (cf.contact_name as string) || '',
        contact_email: (cf.contact_email as string) || '',
        contact_phone: (cf.contact_phone as string) || '',
        tax_id: (cf.tax_id as string) || '',
        contract_start_date: (cf.contract_start_date as string) || '',
        contract_end_date: (cf.contract_end_date as string) || '',
        annual_contract_value: cf.annual_contract_value
          ? String(cf.annual_contract_value)
          : '',
        risk_level: (cf.risk_level as string) || 'medium',
        services_provided: (cf.services_provided as string) || '',
        work_locations: (cf.work_locations as string[]) || [],
        requires_auto_coverage: (cf.requires_auto_coverage as boolean) || false,
        requires_workers_comp:
          cf.requires_workers_comp !== undefined
            ? (cf.requires_workers_comp as boolean)
            : true,
        notes: (cf.notes as string) || '',
      })
    }
  }, [vendor])

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Entity>) => entitiesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entity', id] })
      queryClient.invalidateQueries({ queryKey: ['entities'] })
      router.push(`/vendors/${id}`)
    },
  })

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target
    const newValue =
      type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    setFormData((prev) => ({ ...prev, [name]: newValue }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }))
    }
  }

  const handleWorkLocationChange = (location: string) => {
    setFormData((prev) => ({
      ...prev,
      work_locations: prev.work_locations.includes(location)
        ? prev.work_locations.filter((l) => l !== location)
        : [...prev.work_locations, location],
    }))
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Company name is required'
    }

    if (!formData.vendor_type) {
      newErrors.vendor_type = 'Vendor type is required'
    }

    if (!formData.risk_level) {
      newErrors.risk_level = 'Risk level is required'
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email address'
    }

    if (
      formData.contact_email &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)
    ) {
      newErrors.contact_email = 'Invalid email address'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    const entityData: Partial<Entity> = {
      name: formData.name.trim(),
      description: formData.description.trim() || null,
      email: formData.email.trim() || null,
      phone: formData.phone.trim() || null,
      address: formData.address.trim() || null,
      status: formData.status,
      custom_fields: {
        company_name: formData.name.trim(),
        contact_name: formData.contact_name.trim() || null,
        contact_email: formData.contact_email.trim() || null,
        contact_phone: formData.contact_phone.trim() || null,
        tax_id: formData.tax_id.trim() || null,
        vendor_type: formData.vendor_type,
        contract_start_date: formData.contract_start_date || null,
        contract_end_date: formData.contract_end_date || null,
        annual_contract_value: formData.annual_contract_value
          ? parseFloat(formData.annual_contract_value)
          : null,
        risk_level: formData.risk_level,
        services_provided: formData.services_provided.trim() || null,
        work_locations:
          formData.work_locations.length > 0 ? formData.work_locations : null,
        requires_auto_coverage: formData.requires_auto_coverage,
        requires_workers_comp: formData.requires_workers_comp,
        notes: formData.notes.trim() || null,
      },
    }

    updateMutation.mutate(entityData)
  }

  if (isLoading) {
    return (
      <AuthenticatedLayout>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      </AuthenticatedLayout>
    )
  }

  if (isError || !vendor) {
    return (
      <AuthenticatedLayout>
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">
              Vendor not found
            </h3>
            <p className="text-gray-500 mt-1">
              The vendor you are trying to edit does not exist.
            </p>
            <Link href="/vendors" className="mt-4">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Vendors
              </Button>
            </Link>
          </div>
        </Card>
      </AuthenticatedLayout>
    )
  }

  return (
    <AuthenticatedLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link
            href={`/vendors/${id}`}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Edit Vendor</h1>
            <p className="text-gray-500 mt-1">
              Update {vendor.name}&apos;s information
            </p>
          </div>
        </div>

        {updateMutation.isError && (
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-danger-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-danger-800">
                Failed to update vendor
              </p>
              <p className="text-sm text-danger-600 mt-1">
                {(updateMutation.error as Error)?.message ||
                  'An unexpected error occurred'}
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader
              title="Basic Information"
              description="Enter the vendor's company details"
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name <span className="text-danger-500">*</span>
                </label>
                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter company name"
                  error={errors.name}
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  placeholder="Brief description of the vendor"
                  className="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 placeholder:text-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Vendor Type <span className="text-danger-500">*</span>
                </label>
                <select
                  name="vendor_type"
                  value={formData.vendor_type}
                  onChange={handleChange}
                  className={`block w-full rounded-lg border px-4 py-2.5 text-gray-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 ${
                    errors.vendor_type ? 'border-danger-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select vendor type</option>
                  {vendorTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                {errors.vendor_type && (
                  <p className="mt-1 text-sm text-danger-500">
                    {errors.vendor_type}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Risk Level <span className="text-danger-500">*</span>
                </label>
                <select
                  name="risk_level"
                  value={formData.risk_level}
                  onChange={handleChange}
                  className={`block w-full rounded-lg border px-4 py-2.5 text-gray-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 ${
                    errors.risk_level ? 'border-danger-500' : 'border-gray-300'
                  }`}
                >
                  {riskLevels.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
                {errors.risk_level && (
                  <p className="mt-1 text-sm text-danger-500">
                    {errors.risk_level}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tax ID / EIN
                </label>
                <Input
                  name="tax_id"
                  value={formData.tax_id}
                  onChange={handleChange}
                  placeholder="XX-XXXXXXX"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Address
                </label>
                <Input
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Street address, city, state"
                />
              </div>
            </div>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader
              title="Contact Information"
              description="Primary contact for this vendor"
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Name
                </label>
                <Input
                  name="contact_name"
                  value={formData.contact_name}
                  onChange={handleChange}
                  placeholder="Full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Email
                </label>
                <Input
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="company@example.com"
                  error={errors.email}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Email
                </label>
                <Input
                  name="contact_email"
                  type="email"
                  value={formData.contact_email}
                  onChange={handleChange}
                  placeholder="contact@example.com"
                  error={errors.contact_email}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <Input
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>
          </Card>

          {/* Contract Details */}
          <Card>
            <CardHeader
              title="Contract Details"
              description="Contract information and terms"
            />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contract Start Date
                </label>
                <Input
                  name="contract_start_date"
                  type="date"
                  value={formData.contract_start_date}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contract End Date
                </label>
                <Input
                  name="contract_end_date"
                  type="date"
                  value={formData.contract_end_date}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual Contract Value
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                    $
                  </span>
                  <Input
                    name="annual_contract_value"
                    type="number"
                    value={formData.annual_contract_value}
                    onChange={handleChange}
                    placeholder="0.00"
                    className="pl-7"
                  />
                </div>
              </div>
              <div className="sm:col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Services Provided
                </label>
                <textarea
                  name="services_provided"
                  value={formData.services_provided}
                  onChange={handleChange}
                  rows={2}
                  placeholder="Describe the services this vendor provides"
                  className="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 placeholder:text-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
            </div>
          </Card>

          {/* Compliance Requirements */}
          <Card>
            <CardHeader
              title="Compliance Requirements"
              description="Insurance and coverage requirements"
            />
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Work Locations
                </label>
                <div className="flex flex-wrap gap-2">
                  {workLocationOptions.map((location) => (
                    <label
                      key={location}
                      className={`inline-flex items-center px-4 py-2 rounded-lg border cursor-pointer transition-colors ${
                        formData.work_locations.includes(location)
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={formData.work_locations.includes(location)}
                        onChange={() => handleWorkLocationChange(location)}
                        className="sr-only"
                      />
                      {location}
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-6">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    name="requires_auto_coverage"
                    checked={formData.requires_auto_coverage}
                    onChange={handleChange}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">
                    Requires Auto Coverage
                  </span>
                </label>
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    name="requires_workers_comp"
                    checked={formData.requires_workers_comp}
                    onChange={handleChange}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">
                    Requires Workers Compensation
                  </span>
                </label>
              </div>
            </div>
          </Card>

          {/* Notes */}
          <Card>
            <CardHeader
              title="Additional Notes"
              description="Any additional information about this vendor"
            />
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={4}
              placeholder="Enter any notes or additional information..."
              className="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 placeholder:text-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
            />
          </Card>

          {/* Form Actions */}
          <div className="flex justify-end gap-3">
            <Link href={`/vendors/${id}`}>
              <Button variant="outline" type="button">
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </AuthenticatedLayout>
  )
}
