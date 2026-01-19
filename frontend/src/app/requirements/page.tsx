'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { requirementsApi, entitiesApi, Requirement } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Input, Badge, Card, getStatusVariant } from '@/components/ui'
import {
  Plus,
  Search,
  FileCheck,
  Filter,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  MoreVertical,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  Calendar,
  Eye,
  Trash2,
  Building2,
} from 'lucide-react'

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'compliant', label: 'Compliant' },
  { value: 'expiring_soon', label: 'Expiring Soon' },
  { value: 'expired', label: 'Expired' },
  { value: 'pending', label: 'Pending' },
]

const priorityOptions = [
  { value: '', label: 'All Priorities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

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

const priorityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
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

export default function RequirementsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [page, setPage] = useState(1)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const pageSize = 10

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['requirements', { page, status, priority }],
    queryFn: () =>
      requirementsApi.list({
        page,
        page_size: pageSize,
        status: status || undefined,
        priority: priority || undefined,
      }),
  })

  // Fetch entities for display
  const { data: entities } = useQuery({
    queryKey: ['entities'],
    queryFn: () => entitiesApi.list({ page_size: 100 }),
  })

  const entityMap = new Map(
    entities?.items.map((e) => [e.id, e.name]) || []
  )

  const deleteMutation = useMutation({
    mutationFn: (id: string) => requirementsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requirements'] })
      setOpenMenuId(null)
    },
  })

  const completeMutation = useMutation({
    mutationFn: (id: string) => requirementsApi.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requirements'] })
      setOpenMenuId(null)
    },
  })

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  // Filter by search client-side
  const filteredRequirements = data?.items.filter((req) =>
    search ? req.name.toLowerCase().includes(search.toLowerCase()) : true
  )

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Requirements</h1>
            <p className="text-gray-500 mt-1">
              Track compliance requirements and deadlines
            </p>
          </div>
          <Link href="/requirements/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Requirement
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
                  placeholder="Search requirements..."
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
              <select
                value={priority}
                onChange={(e) => {
                  setPriority(e.target.value)
                  setPage(1)
                }}
                className="block rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-primary-500 focus:ring-primary-500"
              >
                {priorityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </Card>

        {/* Requirements List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : isError ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Failed to load requirements
              </h3>
              <p className="text-gray-500 mt-1">
                {(error as Error)?.message || 'An unexpected error occurred'}
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() =>
                  queryClient.invalidateQueries({ queryKey: ['requirements'] })
                }
              >
                Try Again
              </Button>
            </div>
          </Card>
        ) : filteredRequirements?.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileCheck className="h-12 w-12 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                No requirements found
              </h3>
              <p className="text-gray-500 mt-1">
                {search || status || priority
                  ? 'Try adjusting your search or filter criteria'
                  : 'Get started by adding your first requirement'}
              </p>
              {!search && !status && !priority && (
                <Link href="/requirements/new" className="mt-4">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Requirement
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
                      Requirement
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vendor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Due Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
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
                  {filteredRequirements?.map((req) => {
                    const StatusIcon = statusIcons[req.status] || AlertTriangle
                    const days = daysUntil(req.due_date)
                    return (
                      <tr key={req.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <StatusIcon
                              className={`h-5 w-5 mr-3 ${
                                statusColors[req.status]
                              }`}
                            />
                            <div>
                              <Link
                                href={`/requirements/${req.id}`}
                                className="text-sm font-medium text-gray-900 hover:text-primary-600"
                              >
                                {req.name}
                              </Link>
                              {req.description && (
                                <p className="text-xs text-gray-500 truncate max-w-xs">
                                  {req.description}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {req.entity_id ? (
                            <Link
                              href={`/vendors/${req.entity_id}`}
                              className="flex items-center text-sm text-gray-700 hover:text-primary-600"
                            >
                              <Building2 className="h-4 w-4 mr-1.5 text-gray-400" />
                              {entityMap.get(req.entity_id) || 'Unknown'}
                            </Link>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1.5 text-gray-400" />
                            <span className="text-sm text-gray-900">
                              {formatDate(req.due_date)}
                            </span>
                          </div>
                          {days !== null && (
                            <span
                              className={`text-xs ${
                                days < 0
                                  ? 'text-danger-600'
                                  : days <= 7
                                  ? 'text-warning-600'
                                  : days <= 30
                                  ? 'text-yellow-600'
                                  : 'text-gray-500'
                              }`}
                            >
                              {days < 0
                                ? `${Math.abs(days)} days overdue`
                                : days === 0
                                ? 'Due today'
                                : `${days} days left`}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                              priorityColors[req.priority] ||
                              'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {req.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={getStatusVariant(req.status)}>
                            {req.status.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="relative inline-block text-left">
                            <button
                              onClick={() =>
                                setOpenMenuId(
                                  openMenuId === req.id ? null : req.id
                                )
                              }
                              className="p-2 rounded-lg hover:bg-gray-100"
                            >
                              <MoreVertical className="h-4 w-4 text-gray-500" />
                            </button>
                            {openMenuId === req.id && (
                              <>
                                <div
                                  className="fixed inset-0 z-10"
                                  onClick={() => setOpenMenuId(null)}
                                />
                                <div className="absolute right-0 z-20 mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                                  <div className="py-1">
                                    <Link
                                      href={`/requirements/${req.id}`}
                                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      onClick={() => setOpenMenuId(null)}
                                    >
                                      <Eye className="h-4 w-4 mr-3" />
                                      View Details
                                    </Link>
                                    {req.status !== 'compliant' && (
                                      <button
                                        onClick={() => {
                                          completeMutation.mutate(req.id)
                                        }}
                                        disabled={completeMutation.isPending}
                                        className="flex items-center w-full px-4 py-2 text-sm text-success-700 hover:bg-gray-100"
                                      >
                                        <CheckCircle className="h-4 w-4 mr-3" />
                                        Mark Complete
                                      </button>
                                    )}
                                    <button
                                      onClick={() => {
                                        if (
                                          confirm(
                                            `Are you sure you want to delete "${req.name}"?`
                                          )
                                        ) {
                                          deleteMutation.mutate(req.id)
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
                  {data?.total || 0} requirements
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
