'use client'

import { use } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { requirementsApi, entitiesApi, documentsApi } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Badge, Card, CardHeader, getStatusVariant } from '@/components/ui'
import {
  ArrowLeft,
  Trash2,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  Calendar,
  Building2,
  FileText,
  Upload,
  Edit,
} from 'lucide-react'

interface RequirementDetailPageProps {
  params: Promise<{ id: string }>
}

const statusInfo: Record<
  string,
  { icon: typeof CheckCircle; color: string; bgColor: string; label: string }
> = {
  compliant: {
    icon: CheckCircle,
    color: 'text-success-600',
    bgColor: 'bg-success-50',
    label: 'Compliant',
  },
  expiring_soon: {
    icon: Clock,
    color: 'text-warning-600',
    bgColor: 'bg-warning-50',
    label: 'Expiring Soon',
  },
  expired: {
    icon: XCircle,
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
    label: 'Expired',
  },
  pending: {
    icon: AlertTriangle,
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
    label: 'Pending',
  },
}

const priorityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-green-100 text-green-700 border-green-200',
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function daysUntil(dateString: string | null | undefined): number | null {
  if (!dateString) return null
  const date = new Date(dateString)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diff = date.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export default function RequirementDetailPage({
  params,
}: RequirementDetailPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()

  const {
    data: requirement,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['requirement', id],
    queryFn: () => requirementsApi.get(id),
  })

  const { data: entity } = useQuery({
    queryKey: ['entity', requirement?.entity_id],
    queryFn: () =>
      requirement?.entity_id ? entitiesApi.get(requirement.entity_id) : null,
    enabled: !!requirement?.entity_id,
  })

  const { data: document } = useQuery({
    queryKey: ['document', requirement?.document_id],
    queryFn: () =>
      requirement?.document_id
        ? documentsApi.get(requirement.document_id)
        : null,
    enabled: !!requirement?.document_id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => requirementsApi.delete(id),
    onSuccess: () => {
      router.push('/requirements')
    },
  })

  const completeMutation = useMutation({
    mutationFn: () => requirementsApi.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requirement', id] })
      queryClient.invalidateQueries({ queryKey: ['requirements'] })
    },
  })

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${requirement?.name}"?`)) {
      deleteMutation.mutate()
    }
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

  if (isError || !requirement) {
    return (
      <AuthenticatedLayout>
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">
              Requirement not found
            </h3>
            <p className="text-gray-500 mt-1">
              The requirement you are looking for does not exist or has been
              deleted.
            </p>
            <Link href="/requirements" className="mt-4">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Requirements
              </Button>
            </Link>
          </div>
        </Card>
      </AuthenticatedLayout>
    )
  }

  const status = statusInfo[requirement.status] || statusInfo.pending
  const StatusIcon = status.icon
  const days = daysUntil(requirement.due_date)

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <Link
              href="/requirements"
              className="mt-1 p-2 rounded-lg hover:bg-gray-100"
            >
              <ArrowLeft className="h-5 w-5 text-gray-500" />
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  {requirement.name}
                </h1>
                <Badge variant={getStatusVariant(requirement.status)}>
                  {requirement.status.replace('_', ' ')}
                </Badge>
              </div>
              {requirement.description && (
                <p className="text-gray-500 mt-1">{requirement.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 ml-11 sm:ml-0">
            {requirement.status !== 'compliant' && (
              <Button
                onClick={() => completeMutation.mutate()}
                disabled={completeMutation.isPending}
              >
                {completeMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Mark Complete
              </Button>
            )}
            <Link href={`/requirements/${id}/edit`}>
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
            {/* Status Banner */}
            <Card className={`${status.bgColor} border-0`}>
              <div className="flex items-center gap-4">
                <StatusIcon className={`h-10 w-10 ${status.color}`} />
                <div>
                  <h3 className={`text-lg font-semibold ${status.color}`}>
                    {status.label}
                  </h3>
                  {days !== null && (
                    <p className="text-gray-600">
                      {days < 0
                        ? `This requirement expired ${Math.abs(days)} days ago`
                        : days === 0
                        ? 'This requirement is due today'
                        : days <= 7
                        ? `Only ${days} days remaining`
                        : days <= 30
                        ? `${days} days until due date`
                        : `Due in ${days} days`}
                    </p>
                  )}
                </div>
              </div>
              {requirement.status !== 'compliant' && (
                <div className="mt-4">
                  <Button
                    onClick={() => completeMutation.mutate()}
                    disabled={completeMutation.isPending}
                    size="sm"
                  >
                    {completeMutation.isPending ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <CheckCircle className="h-4 w-4 mr-2" />
                    )}
                    Mark as Complete
                  </Button>
                </div>
              )}
            </Card>

            {/* Requirement Details */}
            <Card>
              <CardHeader
                title="Requirement Details"
                description="Information about this compliance requirement"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Due Date
                  </label>
                  <p className="mt-1 text-sm text-gray-900 flex items-center">
                    <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                    {formatDate(requirement.due_date)}
                  </p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </label>
                  <span
                    className={`mt-1 inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium capitalize border ${
                      priorityColors[requirement.priority] ||
                      'bg-gray-100 text-gray-700 border-gray-200'
                    }`}
                  >
                    {requirement.priority}
                  </span>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Requirement Type
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {requirement.requirement_type_id || '-'}
                  </p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {formatDate(requirement.created_at)}
                  </p>
                </div>
              </div>
            </Card>

            {/* Linked Document */}
            <Card>
              <CardHeader
                title="Linked Document"
                description="Document verifying this requirement"
                action={
                  !document && entity ? (
                    <Link href={`/documents/upload?entity_id=${entity.id}`}>
                      <Button size="sm">
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Document
                      </Button>
                    </Link>
                  ) : undefined
                }
              />
              {document ? (
                <Link
                  href={`/documents/${document.id}`}
                  className="flex items-center gap-4 p-4 -m-4 mt-0 rounded-lg hover:bg-gray-50"
                >
                  <div className="h-12 w-12 flex-shrink-0 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FileText className="h-6 w-6 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">
                      {document.original_filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      Uploaded {formatDate(document.created_at)}
                    </p>
                  </div>
                  <Badge variant={getStatusVariant(document.status)}>
                    {document.status.replace('_', ' ')}
                  </Badge>
                </Link>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <FileText className="h-10 w-10 text-gray-300 mb-3" />
                  <p className="text-sm text-gray-500">No document linked</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Upload a document to verify this requirement
                  </p>
                </div>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Associated Vendor */}
            {entity && (
              <Card>
                <CardHeader title="Associated Vendor" />
                <Link
                  href={`/vendors/${entity.id}`}
                  className="flex items-center gap-3 p-3 -m-3 rounded-lg hover:bg-gray-50"
                >
                  <div className="h-10 w-10 flex-shrink-0 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-primary-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {entity.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(entity.custom_fields?.vendor_type as string) || 'Vendor'}
                    </p>
                  </div>
                </Link>
              </Card>
            )}

            {/* Timeline / Activity */}
            <Card>
              <CardHeader title="Activity" />
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                    <Clock className="h-4 w-4 text-gray-500" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-900">Requirement created</p>
                    <p className="text-xs text-gray-500">
                      {formatDate(requirement.created_at)}
                    </p>
                  </div>
                </div>
                {requirement.updated_at !== requirement.created_at && (
                  <div className="flex gap-3">
                    <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <Edit className="h-4 w-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-900">Last updated</p>
                      <p className="text-xs text-gray-500">
                        {formatDate(requirement.updated_at)}
                      </p>
                    </div>
                  </div>
                )}
                {document && (
                  <div className="flex gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-4 w-4 text-primary-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-900">Document uploaded</p>
                      <p className="text-xs text-gray-500">
                        {formatDate(document.created_at)}
                      </p>
                    </div>
                  </div>
                )}
                {requirement.status === 'compliant' && (
                  <div className="flex gap-3">
                    <div className="h-8 w-8 rounded-full bg-success-100 flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="h-4 w-4 text-success-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-900">Marked compliant</p>
                      <p className="text-xs text-gray-500">
                        {formatDate(requirement.updated_at)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader title="Quick Actions" />
              <div className="space-y-2">
                {entity && (
                  <Link
                    href={`/documents/upload?entity_id=${entity.id}`}
                    className="flex items-center gap-3 p-2 -m-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700"
                  >
                    <Upload className="h-4 w-4 text-gray-400" />
                    Upload Document
                  </Link>
                )}
                <Link
                  href={`/vendors/${entity?.id}`}
                  className="flex items-center gap-3 p-2 -m-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700"
                >
                  <Building2 className="h-4 w-4 text-gray-400" />
                  View Vendor
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
