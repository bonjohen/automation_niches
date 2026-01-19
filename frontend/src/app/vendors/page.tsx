'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { entitiesApi, Entity } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Input, Badge, Card, getStatusVariant } from '@/components/ui'
import {
  Plus,
  Search,
  Building2,
  Mail,
  Phone,
  MoreVertical,
  Filter,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  Trash2,
  Edit,
  Eye,
} from 'lucide-react'

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'pending', label: 'Pending' },
]

const riskLevelColors: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

export default function VendorsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const pageSize = 10

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['entities', { page, status, search }],
    queryFn: () =>
      entitiesApi.list({
        page,
        page_size: pageSize,
        status: status || undefined,
        search: search || undefined,
      }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => entitiesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] })
      setOpenMenuId(null)
    },
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  const getVendorType = (entity: Entity): string => {
    return (entity.custom_fields?.vendor_type as string) || 'Unknown'
  }

  const getRiskLevel = (entity: Entity): string => {
    return (entity.custom_fields?.risk_level as string) || 'medium'
  }

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Vendors</h1>
            <p className="text-gray-500 mt-1">
              Manage your vendors and track their compliance status
            </p>
          </div>
          <Link href="/vendors/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Vendor
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <Card padding="sm">
          <div className="flex flex-col sm:flex-row gap-4">
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search vendors..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </form>
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

        {/* Vendors List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : isError ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Failed to load vendors
              </h3>
              <p className="text-gray-500 mt-1">
                {(error as Error)?.message || 'An unexpected error occurred'}
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() =>
                  queryClient.invalidateQueries({ queryKey: ['entities'] })
                }
              >
                Try Again
              </Button>
            </div>
          </Card>
        ) : data?.items.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Building2 className="h-12 w-12 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                No vendors found
              </h3>
              <p className="text-gray-500 mt-1">
                {search || status
                  ? 'Try adjusting your search or filter criteria'
                  : 'Get started by adding your first vendor'}
              </p>
              {!search && !status && (
                <Link href="/vendors/new" className="mt-4">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Vendor
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
                      Vendor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Level
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
                  {data?.items.map((vendor) => (
                    <tr key={vendor.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0 bg-primary-100 rounded-lg flex items-center justify-center">
                            <Building2 className="h-5 w-5 text-primary-600" />
                          </div>
                          <div className="ml-4">
                            <Link
                              href={`/vendors/${vendor.id}`}
                              className="text-sm font-medium text-gray-900 hover:text-primary-600"
                            >
                              {vendor.name}
                            </Link>
                            {vendor.description && (
                              <p className="text-sm text-gray-500 truncate max-w-xs">
                                {vendor.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">
                          {getVendorType(vendor)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1">
                          {vendor.email && (
                            <a
                              href={`mailto:${vendor.email}`}
                              className="flex items-center text-sm text-gray-500 hover:text-primary-600"
                            >
                              <Mail className="h-3.5 w-3.5 mr-1.5" />
                              {vendor.email}
                            </a>
                          )}
                          {vendor.phone && (
                            <a
                              href={`tel:${vendor.phone}`}
                              className="flex items-center text-sm text-gray-500 hover:text-primary-600"
                            >
                              <Phone className="h-3.5 w-3.5 mr-1.5" />
                              {vendor.phone}
                            </a>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                            riskLevelColors[getRiskLevel(vendor)]
                          }`}
                        >
                          {getRiskLevel(vendor)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={getStatusVariant(vendor.status)}>
                          {vendor.status.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="relative inline-block text-left">
                          <button
                            onClick={() =>
                              setOpenMenuId(
                                openMenuId === vendor.id ? null : vendor.id
                              )
                            }
                            className="p-2 rounded-lg hover:bg-gray-100"
                          >
                            <MoreVertical className="h-4 w-4 text-gray-500" />
                          </button>
                          {openMenuId === vendor.id && (
                            <>
                              <div
                                className="fixed inset-0 z-10"
                                onClick={() => setOpenMenuId(null)}
                              />
                              <div className="absolute right-0 z-20 mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                                <div className="py-1">
                                  <Link
                                    href={`/vendors/${vendor.id}`}
                                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    onClick={() => setOpenMenuId(null)}
                                  >
                                    <Eye className="h-4 w-4 mr-3" />
                                    View Details
                                  </Link>
                                  <Link
                                    href={`/vendors/${vendor.id}/edit`}
                                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    onClick={() => setOpenMenuId(null)}
                                  >
                                    <Edit className="h-4 w-4 mr-3" />
                                    Edit
                                  </Link>
                                  <button
                                    onClick={() => {
                                      if (
                                        confirm(
                                          `Are you sure you want to delete "${vendor.name}"?`
                                        )
                                      ) {
                                        deleteMutation.mutate(vendor.id)
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
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing {(page - 1) * pageSize + 1} to{' '}
                  {Math.min(page * pageSize, data?.total || 0)} of{' '}
                  {data?.total || 0} vendors
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
