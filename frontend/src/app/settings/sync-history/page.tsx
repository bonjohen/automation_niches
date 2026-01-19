'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { ArrowLeft, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react'
import { AuthenticatedLayout } from '@/components/layout'
import { Card, CardHeader, Badge, Button } from '@/components/ui'
import { integrationsApi } from '@/services/api'

function getStatusBadge(status: string) {
  switch (status) {
    case 'success':
      return <Badge variant="success">Success</Badge>
    case 'failed':
      return <Badge variant="danger">Failed</Badge>
    case 'pending':
      return <Badge variant="warning">Pending</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

function getOperationLabel(operation: string) {
  const labels: Record<string, string> = {
    create: 'Create',
    update: 'Update',
    delete: 'Delete',
    compliance_push: 'Compliance Push',
    test_connection: 'Connection Test',
    webhook_received: 'Webhook Received',
    link_external_id: 'Linked External ID',
  }
  return labels[operation] || operation
}

function getDirectionIcon(direction: string) {
  if (direction === 'push') {
    return <span className="text-xs text-gray-500">-></span>
  }
  return <span className="text-xs text-gray-500">&lt;-</span>
}

export default function SyncHistoryPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [providerFilter, setProviderFilter] = useState<string>('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['sync-logs', page, statusFilter, providerFilter],
    queryFn: () => integrationsApi.getSyncLogs({
      page,
      page_size: 20,
      status: statusFilter || undefined,
      provider: providerFilter || undefined,
    }),
  })

  const logs = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / 20)

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/settings/integrations">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Sync History</h1>
              <p className="mt-1 text-sm text-gray-600">
                View all CRM synchronization operations.
              </p>
            </div>
          </div>

          <Button variant="secondary" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <div className="p-4 flex gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="block w-40 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 text-sm"
              >
                <option value="">All</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <select
                value={providerFilter}
                onChange={(e) => { setProviderFilter(e.target.value); setPage(1); }}
                className="block w-40 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 text-sm"
              >
                <option value="">All</option>
                <option value="hubspot">HubSpot</option>
                <option value="zapier">Zapier</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Logs Table */}
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Operation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Direction
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      Loading...
                    </td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      No sync operations found.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="capitalize font-medium">{log.provider}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {getOperationLabel(log.operation)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          {getDirectionIcon(log.direction)}
                          <span className="capitalize">{log.direction}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(log.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {log.duration_ms ? `${log.duration_ms}ms` : '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                        {log.error_message || (log.external_id ? `ID: ${log.external_id}` : '-')}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <p className="text-sm text-gray-700">
                Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} results
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* Stats Summary */}
        {total > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card>
              <div className="p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">{total}</p>
                <p className="text-sm text-gray-600">Total Operations</p>
              </div>
            </Card>
            <Card>
              <div className="p-4 text-center">
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle className="h-5 w-5 text-success-500" />
                  <p className="text-2xl font-bold text-success-600">
                    {logs.filter(l => l.status === 'success').length}
                  </p>
                </div>
                <p className="text-sm text-gray-600">Successful (this page)</p>
              </div>
            </Card>
            <Card>
              <div className="p-4 text-center">
                <div className="flex items-center justify-center gap-2">
                  <XCircle className="h-5 w-5 text-danger-500" />
                  <p className="text-2xl font-bold text-danger-600">
                    {logs.filter(l => l.status === 'failed').length}
                  </p>
                </div>
                <p className="text-sm text-gray-600">Failed (this page)</p>
              </div>
            </Card>
            <Card>
              <div className="p-4 text-center">
                <div className="flex items-center justify-center gap-2">
                  <Clock className="h-5 w-5 text-gray-500" />
                  <p className="text-2xl font-bold text-gray-900">
                    {logs.length > 0
                      ? Math.round(logs.reduce((acc, l) => acc + (l.duration_ms || 0), 0) / logs.length)
                      : 0}ms
                  </p>
                </div>
                <p className="text-sm text-gray-600">Avg Duration</p>
              </div>
            </Card>
          </div>
        )}
      </div>
    </AuthenticatedLayout>
  )
}
