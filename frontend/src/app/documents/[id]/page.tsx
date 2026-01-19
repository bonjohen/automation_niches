'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, entitiesApi } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Badge, Card, CardHeader, Input, getStatusVariant } from '@/components/ui'
import {
  ArrowLeft,
  Trash2,
  FileText,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Download,
  RefreshCw,
  Edit,
  Save,
  X,
  Building2,
  Calendar,
  DollarSign,
  Shield,
  FileCheck,
} from 'lucide-react'

interface DocumentDetailPageProps {
  params: Promise<{ id: string }>
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

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const statusInfo: Record<
  string,
  { icon: typeof CheckCircle; color: string; label: string }
> = {
  pending: { icon: Clock, color: 'text-gray-500', label: 'Pending' },
  processing: { icon: Loader2, color: 'text-primary-500', label: 'Processing' },
  processed: { icon: CheckCircle, color: 'text-success-500', label: 'Processed' },
  failed: { icon: XCircle, color: 'text-danger-500', label: 'Failed' },
  needs_review: { icon: AlertCircle, color: 'text-warning-500', label: 'Needs Review' },
}

// Field definitions for COI extraction display
const coiFields = [
  { key: 'named_insured', label: 'Named Insured', type: 'text' },
  { key: 'policy_number', label: 'Policy Number', type: 'text' },
  { key: 'carrier_name', label: 'Insurance Carrier', type: 'text' },
  { key: 'effective_date', label: 'Effective Date', type: 'date' },
  { key: 'expiration_date', label: 'Expiration Date', type: 'date' },
  { key: 'general_liability_limit', label: 'General Liability (Each Occurrence)', type: 'currency' },
  { key: 'general_aggregate_limit', label: 'General Aggregate Limit', type: 'currency' },
  { key: 'auto_liability_limit', label: 'Auto Liability Limit', type: 'currency' },
  { key: 'workers_comp_coverage', label: 'Has Workers Comp', type: 'boolean' },
  { key: 'workers_comp_limit', label: 'Workers Comp Limit', type: 'currency' },
  { key: 'umbrella_limit', label: 'Umbrella/Excess Limit', type: 'currency' },
  { key: 'certificate_holder', label: 'Certificate Holder', type: 'text' },
  { key: 'additional_insured', label: 'Additional Insured Endorsed', type: 'boolean' },
  { key: 'waiver_of_subrogation', label: 'Waiver of Subrogation', type: 'boolean' },
  { key: 'description_of_operations', label: 'Description of Operations', type: 'text' },
]

export default function DocumentDetailPage({ params }: DocumentDetailPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)
  const [editedData, setEditedData] = useState<Record<string, unknown>>({})

  const {
    data: document,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['document', id],
    queryFn: () => documentsApi.get(id),
  })

  const { data: entity } = useQuery({
    queryKey: ['entity', document?.entity_id],
    queryFn: () =>
      document?.entity_id ? entitiesApi.get(document.entity_id) : null,
    enabled: !!document?.entity_id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => documentsApi.delete(id),
    onSuccess: () => {
      router.push('/documents')
    },
  })

  const processMutation = useMutation({
    mutationFn: () => documentsApi.process(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      documentsApi.update(id, { extracted_data: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] })
      setIsEditing(false)
    },
  })

  const handleDelete = () => {
    if (
      confirm(
        `Are you sure you want to delete "${document?.original_filename}"?`
      )
    ) {
      deleteMutation.mutate()
    }
  }

  const startEditing = () => {
    setEditedData(document?.extracted_data || {})
    setIsEditing(true)
  }

  const cancelEditing = () => {
    setEditedData({})
    setIsEditing(false)
  }

  const saveChanges = () => {
    updateMutation.mutate(editedData)
  }

  const handleFieldChange = (key: string, value: unknown) => {
    setEditedData((prev) => ({ ...prev, [key]: value }))
  }

  const formatValue = (
    value: unknown,
    type: string
  ): string => {
    if (value === null || value === undefined) return '-'
    switch (type) {
      case 'date':
        return formatDate(value as string)
      case 'currency':
        return formatCurrency(value)
      case 'boolean':
        return value ? 'Yes' : 'No'
      default:
        return String(value)
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

  if (isError || !document) {
    return (
      <AuthenticatedLayout>
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">
              Document not found
            </h3>
            <p className="text-gray-500 mt-1">
              The document you are looking for does not exist or has been
              deleted.
            </p>
            <Link href="/documents" className="mt-4">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Documents
              </Button>
            </Link>
          </div>
        </Card>
      </AuthenticatedLayout>
    )
  }

  const status = statusInfo[document.status] || statusInfo.pending
  const StatusIcon = status.icon
  const extractedData = isEditing ? editedData : document.extracted_data || {}
  const hasExtractedData = Object.keys(document.extracted_data || {}).length > 0

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <Link
              href="/documents"
              className="mt-1 p-2 rounded-lg hover:bg-gray-100"
            >
              <ArrowLeft className="h-5 w-5 text-gray-500" />
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  {document.original_filename}
                </h1>
                <Badge variant={getStatusVariant(document.status)}>
                  {document.status.replace('_', ' ')}
                </Badge>
              </div>
              <p className="text-gray-500 mt-1">
                Uploaded {formatDate(document.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 ml-11 sm:ml-0">
            {document.status === 'pending' && (
              <Button
                variant="outline"
                onClick={() => processMutation.mutate()}
                disabled={processMutation.isPending}
              >
                {processMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Process
              </Button>
            )}
            {document.status === 'processed' && !isEditing && (
              <Button variant="outline" onClick={startEditing}>
                <Edit className="h-4 w-4 mr-2" />
                Edit Data
              </Button>
            )}
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
            {/* Processing Status */}
            {document.status === 'processing' && (
              <Card className="bg-primary-50 border-primary-200">
                <div className="flex items-center gap-4">
                  <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
                  <div>
                    <h3 className="text-lg font-medium text-primary-800">
                      Processing Document
                    </h3>
                    <p className="text-primary-600">
                      AI is extracting data from this document. This may take a
                      moment...
                    </p>
                  </div>
                </div>
              </Card>
            )}

            {/* Failed Status */}
            {document.status === 'failed' && (
              <Card className="bg-danger-50 border-danger-200">
                <div className="flex items-center gap-4">
                  <XCircle className="h-8 w-8 text-danger-500" />
                  <div>
                    <h3 className="text-lg font-medium text-danger-800">
                      Processing Failed
                    </h3>
                    <p className="text-danger-600">
                      We couldn&apos;t extract data from this document. Try
                      uploading a clearer image or PDF.
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => processMutation.mutate()}
                  disabled={processMutation.isPending}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry Processing
                </Button>
              </Card>
            )}

            {/* Extracted Data */}
            {(hasExtractedData || document.status === 'processed') && (
              <Card>
                <CardHeader
                  title="Extracted Data"
                  description={
                    isEditing
                      ? 'Edit the extracted information below'
                      : 'Information extracted from the document'
                  }
                  action={
                    isEditing ? (
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={cancelEditing}
                        >
                          <X className="h-4 w-4 mr-2" />
                          Cancel
                        </Button>
                        <Button
                          size="sm"
                          onClick={saveChanges}
                          disabled={updateMutation.isPending}
                        >
                          {updateMutation.isPending ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <Save className="h-4 w-4 mr-2" />
                          )}
                          Save
                        </Button>
                      </div>
                    ) : undefined
                  }
                />
                {document.extraction_confidence !== null && (
                  <div className="mb-4 flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          document.extraction_confidence >= 0.8
                            ? 'bg-success-500'
                            : document.extraction_confidence >= 0.6
                            ? 'bg-warning-500'
                            : 'bg-danger-500'
                        }`}
                        style={{
                          width: `${document.extraction_confidence * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm text-gray-500">
                      {Math.round(document.extraction_confidence * 100)}%
                      confidence
                    </span>
                  </div>
                )}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {coiFields.map((field) => (
                    <div
                      key={field.key}
                      className={
                        field.type === 'text' &&
                        field.key === 'description_of_operations'
                          ? 'sm:col-span-2'
                          : ''
                      }
                    >
                      <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                        {field.label}
                      </label>
                      {isEditing ? (
                        field.type === 'boolean' ? (
                          <select
                            value={
                              extractedData[field.key] === true
                                ? 'true'
                                : extractedData[field.key] === false
                                ? 'false'
                                : ''
                            }
                            onChange={(e) =>
                              handleFieldChange(
                                field.key,
                                e.target.value === ''
                                  ? null
                                  : e.target.value === 'true'
                              )
                            }
                            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-primary-500"
                          >
                            <option value="">Not specified</option>
                            <option value="true">Yes</option>
                            <option value="false">No</option>
                          </select>
                        ) : field.type === 'date' ? (
                          <Input
                            type="date"
                            value={(extractedData[field.key] as string) || ''}
                            onChange={(e) =>
                              handleFieldChange(
                                field.key,
                                e.target.value || null
                              )
                            }
                          />
                        ) : field.type === 'currency' ? (
                          <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                              $
                            </span>
                            <Input
                              type="number"
                              value={
                                extractedData[field.key] !== null
                                  ? String(extractedData[field.key])
                                  : ''
                              }
                              onChange={(e) =>
                                handleFieldChange(
                                  field.key,
                                  e.target.value
                                    ? parseFloat(e.target.value)
                                    : null
                                )
                              }
                              className="pl-7"
                            />
                          </div>
                        ) : (
                          <Input
                            type="text"
                            value={(extractedData[field.key] as string) || ''}
                            onChange={(e) =>
                              handleFieldChange(
                                field.key,
                                e.target.value || null
                              )
                            }
                          />
                        )
                      ) : (
                        <p className="text-sm text-gray-900">
                          {formatValue(extractedData[field.key], field.type)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Document Preview Placeholder */}
            <Card>
              <CardHeader
                title="Document Preview"
                description="View the original document"
              />
              <div className="aspect-[4/3] bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">
                    Document preview not available
                  </p>
                  <Button variant="outline" size="sm" className="mt-4">
                    <Download className="h-4 w-4 mr-2" />
                    Download Original
                  </Button>
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Document Info */}
            <Card>
              <CardHeader title="Document Info" />
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </label>
                  <div className="mt-1 flex items-center gap-2">
                    <StatusIcon
                      className={`h-5 w-5 ${status.color} ${
                        document.status === 'processing' ? 'animate-spin' : ''
                      }`}
                    />
                    <span className="text-sm font-medium text-gray-900">
                      {status.label}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File Type
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {document.mime_type.split('/')[1]?.toUpperCase() ||
                      document.mime_type}
                  </p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File Size
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {formatFileSize(document.file_size)}
                  </p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {formatDate(document.created_at)}
                  </p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Updated
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {formatDate(document.updated_at)}
                  </p>
                </div>
              </div>
            </Card>

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

            {/* Quick Stats from Extracted Data */}
            {hasExtractedData && (
              <Card>
                <CardHeader title="Coverage Summary" />
                <div className="space-y-3">
                  {extractedData.expiration_date && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500 flex items-center">
                        <Calendar className="h-4 w-4 mr-2" />
                        Expires
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatDate(extractedData.expiration_date as string)}
                      </span>
                    </div>
                  )}
                  {extractedData.general_liability_limit && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500 flex items-center">
                        <Shield className="h-4 w-4 mr-2" />
                        GL Limit
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(extractedData.general_liability_limit)}
                      </span>
                    </div>
                  )}
                  {extractedData.additional_insured !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500 flex items-center">
                        <FileCheck className="h-4 w-4 mr-2" />
                        Add&apos;l Insured
                      </span>
                      <Badge
                        variant={
                          extractedData.additional_insured ? 'success' : 'gray'
                        }
                      >
                        {extractedData.additional_insured ? 'Yes' : 'No'}
                      </Badge>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
