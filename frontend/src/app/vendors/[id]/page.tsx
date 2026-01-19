'use client'

import { use } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  entitiesApi,
  requirementsApi,
  documentsApi,
  Entity,
  Requirement,
  Document,
} from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Badge, Card, CardHeader, getStatusVariant } from '@/components/ui'
import {
  ArrowLeft,
  Edit,
  Trash2,
  Building2,
  Mail,
  Phone,
  MapPin,
  Calendar,
  DollarSign,
  FileCheck,
  Upload,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Loader2,
  AlertCircle,
  FileText,
  ExternalLink,
} from 'lucide-react'

interface VendorDetailPageProps {
  params: Promise<{ id: string }>
}

const riskLevelColors: Record<string, string> = {
  low: 'bg-green-100 text-green-700 border-green-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
}

const statusIcons: Record<string, typeof CheckCircle> = {
  compliant: CheckCircle,
  expiring_soon: Clock,
  expired: XCircle,
  pending: AlertTriangle,
}

const statusColors: Record<string, string> = {
  compliant: 'text-success-600',
  expiring_soon: 'text-warning-600',
  expired: 'text-danger-600',
  pending: 'text-gray-500',
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatCurrency(value: unknown): string {
  if (value === null || value === undefined) return '-'
  const num = typeof value === 'number' ? value : parseFloat(String(value))
  if (isNaN(num)) return '-'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(num)
}

function daysUntil(dateString: string | null | undefined): number | null {
  if (!dateString) return null
  const date = new Date(dateString)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diff = date.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export default function VendorDetailPage({ params }: VendorDetailPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()

  const {
    data: vendor,
    isLoading: vendorLoading,
    isError: vendorError,
  } = useQuery({
    queryKey: ['entity', id],
    queryFn: () => entitiesApi.get(id),
  })

  const { data: requirements, isLoading: requirementsLoading } = useQuery({
    queryKey: ['requirements', { entity_id: id }],
    queryFn: () => requirementsApi.list({ entity_id: id }),
    enabled: !!vendor,
  })

  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents', { entity_id: id }],
    queryFn: () => documentsApi.list({ entity_id: id }),
    enabled: !!vendor,
  })

  const deleteMutation = useMutation({
    mutationFn: () => entitiesApi.delete(id),
    onSuccess: () => {
      router.push('/vendors')
    },
  })

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${vendor?.name}"?`)) {
      deleteMutation.mutate()
    }
  }

  if (vendorLoading) {
    return (
      <AuthenticatedLayout>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      </AuthenticatedLayout>
    )
  }

  if (vendorError || !vendor) {
    return (
      <AuthenticatedLayout>
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">
              Vendor not found
            </h3>
            <p className="text-gray-500 mt-1">
              The vendor you are looking for does not exist or has been deleted.
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

  const customFields = vendor.custom_fields || {}
  const riskLevel = (customFields.risk_level as string) || 'medium'

  // Calculate compliance summary
  const complianceSummary = {
    total: requirements?.items.length || 0,
    compliant: requirements?.items.filter((r) => r.status === 'compliant').length || 0,
    expiringSoon:
      requirements?.items.filter((r) => r.status === 'expiring_soon').length || 0,
    expired: requirements?.items.filter((r) => r.status === 'expired').length || 0,
    pending: requirements?.items.filter((r) => r.status === 'pending').length || 0,
  }

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <Link
              href="/vendors"
              className="mt-1 p-2 rounded-lg hover:bg-gray-100"
            >
              <ArrowLeft className="h-5 w-5 text-gray-500" />
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  {vendor.name}
                </h1>
                <Badge variant={getStatusVariant(vendor.status)}>
                  {vendor.status.replace('_', ' ')}
                </Badge>
              </div>
              {vendor.description && (
                <p className="text-gray-500 mt-1">{vendor.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 ml-11 sm:ml-0">
            <Link href={`/vendors/${id}/edit`}>
              <Button variant="outline">
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            </Link>
            <Button
              variant="outline"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="text-danger-600 hover:bg-danger-50"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Vendor Information */}
            <Card>
              <CardHeader
                title="Vendor Information"
                description="Contact and business details"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vendor Type
                    </label>
                    <p className="mt-1 text-sm text-gray-900">
                      {customFields.vendor_type || '-'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact Name
                    </label>
                    <p className="mt-1 text-sm text-gray-900">
                      {customFields.contact_name || '-'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </label>
                    <p className="mt-1">
                      {vendor.email ? (
                        <a
                          href={`mailto:${vendor.email}`}
                          className="text-sm text-primary-600 hover:underline flex items-center"
                        >
                          <Mail className="h-4 w-4 mr-1.5" />
                          {vendor.email}
                        </a>
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Phone
                    </label>
                    <p className="mt-1">
                      {vendor.phone ? (
                        <a
                          href={`tel:${vendor.phone}`}
                          className="text-sm text-primary-600 hover:underline flex items-center"
                        >
                          <Phone className="h-4 w-4 mr-1.5" />
                          {vendor.phone}
                        </a>
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Address
                    </label>
                    <p className="mt-1 text-sm text-gray-900 flex items-start">
                      {vendor.address ? (
                        <>
                          <MapPin className="h-4 w-4 mr-1.5 mt-0.5 flex-shrink-0 text-gray-400" />
                          {vendor.address}
                        </>
                      ) : (
                        '-'
                      )}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tax ID / EIN
                    </label>
                    <p className="mt-1 text-sm text-gray-900">
                      {customFields.tax_id || '-'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Services Provided
                    </label>
                    <p className="mt-1 text-sm text-gray-900">
                      {customFields.services_provided || '-'}
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Contract Details */}
            <Card>
              <CardHeader title="Contract Details" />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contract Start Date
                  </label>
                  <p className="mt-1 text-sm text-gray-900 flex items-center">
                    <Calendar className="h-4 w-4 mr-1.5 text-gray-400" />
                    {formatDate(customFields.contract_start_date as string)}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contract End Date
                  </label>
                  <p className="mt-1 text-sm text-gray-900 flex items-center">
                    <Calendar className="h-4 w-4 mr-1.5 text-gray-400" />
                    {formatDate(customFields.contract_end_date as string)}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Annual Contract Value
                  </label>
                  <p className="mt-1 text-sm text-gray-900 flex items-center">
                    <DollarSign className="h-4 w-4 mr-1.5 text-gray-400" />
                    {formatCurrency(customFields.annual_contract_value)}
                  </p>
                </div>
              </div>
            </Card>

            {/* Requirements */}
            <Card padding="none">
              <div className="p-6 border-b border-gray-200">
                <CardHeader
                  title="Compliance Requirements"
                  description="Track insurance and compliance requirements"
                  action={
                    <Link href={`/requirements/new?entity_id=${id}`}>
                      <Button size="sm">
                        <FileCheck className="h-4 w-4 mr-2" />
                        Add Requirement
                      </Button>
                    </Link>
                  }
                />
              </div>
              {requirementsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                </div>
              ) : requirements?.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center px-6">
                  <FileCheck className="h-10 w-10 text-gray-300 mb-3" />
                  <p className="text-sm text-gray-500">
                    No compliance requirements yet
                  </p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {requirements?.items.map((req) => {
                    const Icon = statusIcons[req.status] || AlertTriangle
                    const days = daysUntil(req.due_date)
                    return (
                      <li key={req.id}>
                        <Link
                          href={`/requirements/${req.id}`}
                          className="flex items-center justify-between px-6 py-4 hover:bg-gray-50"
                        >
                          <div className="flex items-center gap-3">
                            <Icon
                              className={`h-5 w-5 ${statusColors[req.status]}`}
                            />
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {req.name}
                              </p>
                              <p className="text-xs text-gray-500">
                                Due: {formatDate(req.due_date)}
                                {days !== null && days <= 30 && days >= 0 && (
                                  <span className="ml-2 text-warning-600">
                                    ({days} days left)
                                  </span>
                                )}
                                {days !== null && days < 0 && (
                                  <span className="ml-2 text-danger-600">
                                    ({Math.abs(days)} days overdue)
                                  </span>
                                )}
                              </p>
                            </div>
                          </div>
                          <Badge variant={getStatusVariant(req.status)}>
                            {req.status.replace('_', ' ')}
                          </Badge>
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              )}
            </Card>

            {/* Documents */}
            <Card padding="none">
              <div className="p-6 border-b border-gray-200">
                <CardHeader
                  title="Documents"
                  description="Uploaded certificates and documents"
                  action={
                    <Link href={`/documents/upload?entity_id=${id}`}>
                      <Button size="sm">
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Document
                      </Button>
                    </Link>
                  }
                />
              </div>
              {documentsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                </div>
              ) : documents?.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center px-6">
                  <FileText className="h-10 w-10 text-gray-300 mb-3" />
                  <p className="text-sm text-gray-500">No documents uploaded</p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {documents?.items.map((doc) => (
                    <li key={doc.id}>
                      <Link
                        href={`/documents/${doc.id}`}
                        className="flex items-center justify-between px-6 py-4 hover:bg-gray-50"
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {doc.original_filename}
                            </p>
                            <p className="text-xs text-gray-500">
                              Uploaded {formatDate(doc.created_at)}
                            </p>
                          </div>
                        </div>
                        <Badge variant={getStatusVariant(doc.status)}>
                          {doc.status.replace('_', ' ')}
                        </Badge>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Compliance Status */}
            <Card>
              <CardHeader title="Compliance Status" />
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Risk Level</span>
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium capitalize border ${riskLevelColors[riskLevel]}`}
                  >
                    {riskLevel}
                  </span>
                </div>
                <div className="pt-4 border-t border-gray-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 flex items-center">
                      <CheckCircle className="h-4 w-4 mr-2 text-success-500" />
                      Compliant
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {complianceSummary.compliant}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 flex items-center">
                      <Clock className="h-4 w-4 mr-2 text-warning-500" />
                      Expiring Soon
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {complianceSummary.expiringSoon}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 flex items-center">
                      <XCircle className="h-4 w-4 mr-2 text-danger-500" />
                      Expired
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {complianceSummary.expired}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 flex items-center">
                      <AlertTriangle className="h-4 w-4 mr-2 text-gray-400" />
                      Pending
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {complianceSummary.pending}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Coverage Requirements */}
            <Card>
              <CardHeader title="Coverage Requirements" />
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Auto Coverage</span>
                  <Badge
                    variant={
                      customFields.requires_auto_coverage ? 'warning' : 'gray'
                    }
                  >
                    {customFields.requires_auto_coverage
                      ? 'Required'
                      : 'Not Required'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Workers Comp</span>
                  <Badge
                    variant={
                      customFields.requires_workers_comp ? 'warning' : 'gray'
                    }
                  >
                    {customFields.requires_workers_comp
                      ? 'Required'
                      : 'Not Required'}
                  </Badge>
                </div>
              </div>
            </Card>

            {/* Work Locations */}
            {customFields.work_locations &&
              Array.isArray(customFields.work_locations) &&
              customFields.work_locations.length > 0 && (
                <Card>
                  <CardHeader title="Work Locations" />
                  <div className="flex flex-wrap gap-2">
                    {(customFields.work_locations as string[]).map(
                      (location) => (
                        <Badge key={location} variant="gray">
                          {location}
                        </Badge>
                      )
                    )}
                  </div>
                </Card>
              )}

            {/* Notes */}
            {customFields.notes && (
              <Card>
                <CardHeader title="Notes" />
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {customFields.notes}
                </p>
              </Card>
            )}

            {/* Metadata */}
            <Card>
              <CardHeader title="Record Info" />
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Created</span>
                  <span className="text-gray-900">
                    {formatDate(vendor.created_at)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Last Updated</span>
                  <span className="text-gray-900">
                    {formatDate(vendor.updated_at)}
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
