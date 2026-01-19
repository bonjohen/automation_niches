'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, Document } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Input, Badge, Card, getStatusVariant } from '@/components/ui'
import {
  Plus,
  Search,
  FileText,
  Filter,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  Trash2,
  Eye,
  MoreVertical,
  Upload,
  File,
  Image,
  FileImage,
} from 'lucide-react'

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'processed', label: 'Processed' },
  { value: 'failed', label: 'Failed' },
  { value: 'needs_review', label: 'Needs Review' },
]

function getFileIcon(mimeType: string) {
  if (mimeType.startsWith('image/')) return FileImage
  if (mimeType === 'application/pdf') return FileText
  return File
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const pageSize = 10

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['documents', { page, status }],
    queryFn: () =>
      documentsApi.list({
        page,
        page_size: pageSize,
        status: status || undefined,
      }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setOpenMenuId(null)
    },
  })

  const processMutation = useMutation({
    mutationFn: (id: string) => documentsApi.process(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  // Filter documents client-side for search (since API might not support text search)
  const filteredDocuments = data?.items.filter((doc) =>
    search
      ? doc.original_filename.toLowerCase().includes(search.toLowerCase())
      : true
  )

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
            <p className="text-gray-500 mt-1">
              Upload and manage compliance documents
            </p>
          </div>
          <Link href="/documents/upload">
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <Card padding="sm">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search documents..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value)
                  setPage(1)
                }}
                className="block rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-primary-500 focus:ring-primary-500"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </Card>

        {/* Documents List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : isError ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Failed to load documents
              </h3>
              <p className="text-gray-500 mt-1">
                {(error as Error)?.message || 'An unexpected error occurred'}
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() =>
                  queryClient.invalidateQueries({ queryKey: ['documents'] })
                }
              >
                Try Again
              </Button>
            </div>
          </Card>
        ) : filteredDocuments?.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                No documents found
              </h3>
              <p className="text-gray-500 mt-1">
                {search || status
                  ? 'Try adjusting your search or filter criteria'
                  : 'Get started by uploading your first document'}
              </p>
              {!search && !status && (
                <Link href="/documents/upload" className="mt-4">
                  <Button>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Document
                  </Button>
                </Link>
              )}
            </div>
          </Card>
        ) : (
          <>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Document
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Uploaded
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredDocuments?.map((doc) => {
                    const FileIcon = getFileIcon(doc.mime_type)
                    return (
                      <tr key={doc.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="h-10 w-10 flex-shrink-0 bg-gray-100 rounded-lg flex items-center justify-center">
                              <FileIcon className="h-5 w-5 text-gray-500" />
                            </div>
                            <div className="ml-4">
                              <Link
                                href={`/documents/${doc.id}`}
                                className="text-sm font-medium text-gray-900 hover:text-primary-600"
                              >
                                {doc.original_filename}
                              </Link>
                              {doc.extraction_confidence !== null && (
                                <p className="text-xs text-gray-500">
                                  Confidence:{' '}
                                  {Math.round(doc.extraction_confidence * 100)}%
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-500">
                            {doc.mime_type.split('/')[1]?.toUpperCase() ||
                              doc.mime_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-500">
                            {formatFileSize(doc.file_size)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-500">
                            {formatDate(doc.created_at)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={getStatusVariant(doc.status)}>
                            {doc.status.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="relative inline-block text-left">
                            <button
                              onClick={() =>
                                setOpenMenuId(
                                  openMenuId === doc.id ? null : doc.id
                                )
                              }
                              className="p-2 rounded-lg hover:bg-gray-100"
                            >
                              <MoreVertical className="h-4 w-4 text-gray-500" />
                            </button>
                            {openMenuId === doc.id && (
                              <>
                                <div
                                  className="fixed inset-0 z-10"
                                  onClick={() => setOpenMenuId(null)}
                                />
                                <div className="absolute right-0 z-20 mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                                  <div className="py-1">
                                    <Link
                                      href={`/documents/${doc.id}`}
                                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      onClick={() => setOpenMenuId(null)}
                                    >
                                      <Eye className="h-4 w-4 mr-3" />
                                      View Details
                                    </Link>
                                    {doc.status === 'pending' && (
                                      <button
                                        onClick={() => {
                                          processMutation.mutate(doc.id)
                                          setOpenMenuId(null)
                                        }}
                                        disabled={processMutation.isPending}
                                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      >
                                        <Loader2
                                          className={`h-4 w-4 mr-3 ${
                                            processMutation.isPending
                                              ? 'animate-spin'
                                              : ''
                                          }`}
                                        />
                                        Process Document
                                      </button>
                                    )}
                                    <button
                                      onClick={() => {
                                        if (
                                          confirm(
                                            `Are you sure you want to delete "${doc.original_filename}"?`
                                          )
                                        ) {
                                          deleteMutation.mutate(doc.id)
                                        }
                                      }}
                                      disabled={deleteMutation.isPending}
                                      className="flex items-center w-full px-4 py-2 text-sm text-danger-600 hover:bg-gray-100"
                                    >
                                      <Trash2 className="h-4 w-4 mr-3" />
                                      Delete
                                    </button>
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing {(page - 1) * pageSize + 1} to{' '}
                  {Math.min(page * pageSize, data?.total || 0)} of{' '}
                  {data?.total || 0} documents
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-gray-700">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AuthenticatedLayout>
  )
}
