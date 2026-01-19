'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi, Notification } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Badge, Card, getStatusVariant } from '@/components/ui'
import {
  Bell,
  BellOff,
  Filter,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  AlertTriangle,
  Mail,
  MailOpen,
  Trash2,
  Check,
} from 'lucide-react'

const typeOptions = [
  { value: '', label: 'All Types' },
  { value: 'reminder', label: 'Reminders' },
  { value: 'expiring', label: 'Expiring' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'status_change', label: 'Status Changes' },
  { value: 'escalation', label: 'Escalations' },
]

const typeIcons: Record<string, typeof Bell> = {
  reminder: Bell,
  expiring: Clock,
  overdue: AlertTriangle,
  status_change: CheckCircle,
  escalation: AlertCircle,
}

const typeColors: Record<string, string> = {
  reminder: 'bg-primary-100 text-primary-600',
  expiring: 'bg-warning-100 text-warning-600',
  overdue: 'bg-danger-100 text-danger-600',
  status_change: 'bg-success-100 text-success-600',
  escalation: 'bg-orange-100 text-orange-600',
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // Less than 1 hour
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return minutes <= 1 ? 'Just now' : `${minutes} minutes ago`
  }

  // Less than 24 hours
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours} hour${hours === 1 ? '' : 's'} ago`
  }

  // Less than 7 days
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days} day${days === 1 ? '' : 's'} ago`
  }

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export default function NotificationsPage() {
  const queryClient = useQueryClient()
  const [type, setType] = useState('')
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['notifications', { page, type, unreadOnly }],
    queryFn: () =>
      notificationsApi.list({
        page,
        page_size: pageSize,
        notification_type: type || undefined,
        unread_only: unreadOnly || undefined,
      }),
  })

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0
  const unreadCount = data?.unread_count || 0

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
            <p className="text-gray-500 mt-1">
              {unreadCount > 0
                ? `You have ${unreadCount} unread notification${
                    unreadCount === 1 ? '' : 's'
                  }`
                : 'All caught up!'}
            </p>
          </div>
          {unreadCount > 0 && (
            <Button
              variant="outline"
              onClick={() => markAllReadMutation.mutate()}
              disabled={markAllReadMutation.isPending}
            >
              {markAllReadMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              Mark All as Read
            </Button>
          )}
        </div>

        {/* Filters */}
        <Card padding="sm">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={type}
                onChange={(e) => {
                  setType(e.target.value)
                  setPage(1)
                }}
                className="block rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-primary-500 focus:ring-primary-500"
              >
                {typeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => {
                  setUnreadOnly(e.target.checked)
                  setPage(1)
                }}
                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              Show unread only
            </label>
          </div>
        </Card>

        {/* Notifications List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : isError ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="h-12 w-12 text-danger-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Failed to load notifications
              </h3>
              <p className="text-gray-500 mt-1">
                {(error as Error)?.message || 'An unexpected error occurred'}
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() =>
                  queryClient.invalidateQueries({ queryKey: ['notifications'] })
                }
              >
                Try Again
              </Button>
            </div>
          </Card>
        ) : data?.items.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <BellOff className="h-12 w-12 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                No notifications
              </h3>
              <p className="text-gray-500 mt-1">
                {type || unreadOnly
                  ? 'Try adjusting your filter criteria'
                  : "You're all caught up! Check back later for updates."}
              </p>
            </div>
          </Card>
        ) : (
          <>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden divide-y divide-gray-200">
              {data?.items.map((notification) => {
                const TypeIcon =
                  typeIcons[notification.notification_type] || Bell
                const isUnread = !notification.read_at
                return (
                  <div
                    key={notification.id}
                    className={`p-4 flex gap-4 ${
                      isUnread ? 'bg-primary-50/50' : ''
                    }`}
                  >
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                        typeColors[notification.notification_type] ||
                        'bg-gray-100 text-gray-600'
                      }`}
                    >
                      <TypeIcon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p
                            className={`text-sm ${
                              isUnread
                                ? 'font-semibold text-gray-900'
                                : 'text-gray-900'
                            }`}
                          >
                            {notification.subject}
                          </p>
                          <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                            {notification.body.replace(/<[^>]*>/g, '')}
                          </p>
                          <p className="text-xs text-gray-400 mt-2">
                            {formatDate(notification.scheduled_at)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {isUnread && (
                            <button
                              onClick={() =>
                                markReadMutation.mutate(notification.id)
                              }
                              disabled={markReadMutation.isPending}
                              className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                              title="Mark as read"
                            >
                              <MailOpen className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => {
                              if (
                                confirm(
                                  'Are you sure you want to delete this notification?'
                                )
                              ) {
                                deleteMutation.mutate(notification.id)
                              }
                            }}
                            disabled={deleteMutation.isPending}
                            className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-danger-600"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                    {isUnread && (
                      <div className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0 mt-2" />
                    )}
                  </div>
                )
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing {(page - 1) * pageSize + 1} to{' '}
                  {Math.min(page * pageSize, data?.total || 0)} of{' '}
                  {data?.total || 0} notifications
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
