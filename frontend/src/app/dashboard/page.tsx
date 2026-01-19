'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Building2,
  FileCheck,
  Upload,
  ArrowRight,
  TrendingUp,
} from 'lucide-react'
import { AuthenticatedLayout } from '@/components/layout'
import { Card, CardHeader, Badge, Button, getStatusVariant } from '@/components/ui'
import { requirementsApi, entitiesApi, documentsApi } from '@/services/api'

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  href,
}: {
  title: string
  value: number
  icon: React.ElementType
  color: 'success' | 'warning' | 'danger' | 'primary' | 'gray'
  href: string
}) {
  const colorClasses = {
    success: 'bg-success-100 text-success-600',
    warning: 'bg-warning-100 text-warning-600',
    danger: 'bg-danger-100 text-danger-600',
    primary: 'bg-primary-100 text-primary-600',
    gray: 'bg-gray-100 text-gray-600',
  }

  return (
    <Link href={href}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
            </div>
            <div className={`rounded-full p-3 ${colorClasses[color]}`}>
              <Icon className="h-6 w-6" />
            </div>
          </div>
        </div>
      </Card>
    </Link>
  )
}

function ComplianceChart({ summary }: { summary: { compliant: number; expiring_soon: number; expired: number; pending: number } }) {
  const total = summary.compliant + summary.expiring_soon + summary.expired + summary.pending
  if (total === 0) return null

  const compliantPercent = (summary.compliant / total) * 100
  const expiringPercent = (summary.expiring_soon / total) * 100
  const expiredPercent = (summary.expired / total) * 100
  const pendingPercent = (summary.pending / total) * 100

  return (
    <div className="mt-4">
      <div className="flex h-4 overflow-hidden rounded-full bg-gray-200">
        {compliantPercent > 0 && (
          <div
            className="bg-success-500 transition-all duration-500"
            style={{ width: `${compliantPercent}%` }}
          />
        )}
        {expiringPercent > 0 && (
          <div
            className="bg-warning-500 transition-all duration-500"
            style={{ width: `${expiringPercent}%` }}
          />
        )}
        {expiredPercent > 0 && (
          <div
            className="bg-danger-500 transition-all duration-500"
            style={{ width: `${expiredPercent}%` }}
          />
        )}
        {pendingPercent > 0 && (
          <div
            className="bg-gray-400 transition-all duration-500"
            style={{ width: `${pendingPercent}%` }}
          />
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-success-500" />
          <span className="text-gray-600">Compliant ({summary.compliant})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-warning-500" />
          <span className="text-gray-600">Expiring Soon ({summary.expiring_soon})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-danger-500" />
          <span className="text-gray-600">Expired ({summary.expired})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-gray-400" />
          <span className="text-gray-600">Pending ({summary.pending})</span>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['requirements', 'summary'],
    queryFn: () => requirementsApi.getSummary(),
  })

  const { data: recentRequirements } = useQuery({
    queryKey: ['requirements', 'recent'],
    queryFn: () => requirementsApi.list({ page_size: 5, status: 'EXPIRING_SOON' }),
  })

  const { data: entities } = useQuery({
    queryKey: ['entities', 'list'],
    queryFn: () => entitiesApi.list({ page_size: 100 }),
  })

  const { data: recentDocuments } = useQuery({
    queryKey: ['documents', 'recent'],
    queryFn: () => documentsApi.list({ page_size: 5 }),
  })

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-1 text-sm text-gray-600">
              Overview of your compliance status
            </p>
          </div>
          <Link href="/vendors/new">
            <Button leftIcon={<Building2 className="h-4 w-4" />}>
              Add Vendor
            </Button>
          </Link>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Compliant"
            value={summary?.compliant || 0}
            icon={CheckCircle}
            color="success"
            href="/requirements?status=COMPLIANT"
          />
          <StatCard
            title="Expiring Soon"
            value={summary?.expiring_soon || 0}
            icon={AlertTriangle}
            color="warning"
            href="/requirements?status=EXPIRING_SOON"
          />
          <StatCard
            title="Expired"
            value={summary?.expired || 0}
            icon={XCircle}
            color="danger"
            href="/requirements?status=EXPIRED"
          />
          <StatCard
            title="Pending"
            value={summary?.pending || 0}
            icon={Clock}
            color="gray"
            href="/requirements?status=PENDING"
          />
        </div>

        {/* Compliance overview chart */}
        <Card>
          <CardHeader
            title="Compliance Overview"
            description="Overall compliance status across all vendors"
          />
          <div className="px-6 pb-6">
            {summary && <ComplianceChart summary={summary} />}
            {summaryLoading && (
              <div className="h-20 animate-pulse rounded bg-gray-200" />
            )}
          </div>
        </Card>

        {/* Two column layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Expiring soon */}
          <Card>
            <CardHeader
              title="Expiring Soon"
              description="Requirements expiring in the next 30 days"
              action={
                <Link href="/requirements?status=EXPIRING_SOON">
                  <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="h-4 w-4" />}>
                    View all
                  </Button>
                </Link>
              }
            />
            <div className="divide-y divide-gray-200">
              {recentRequirements?.items.length === 0 && (
                <div className="px-6 py-8 text-center text-sm text-gray-500">
                  No requirements expiring soon
                </div>
              )}
              {recentRequirements?.items.map((req) => (
                <Link
                  key={req.id}
                  href={`/requirements/${req.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50"
                >
                  <div>
                    <p className="font-medium text-gray-900">{req.name}</p>
                    <p className="text-sm text-gray-500">
                      Due: {req.due_date ? new Date(req.due_date).toLocaleDateString() : 'No date'}
                    </p>
                  </div>
                  <Badge variant={getStatusVariant(req.status)}>{req.status}</Badge>
                </Link>
              ))}
            </div>
          </Card>

          {/* Recent documents */}
          <Card>
            <CardHeader
              title="Recent Documents"
              description="Recently uploaded documents"
              action={
                <Link href="/documents">
                  <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="h-4 w-4" />}>
                    View all
                  </Button>
                </Link>
              }
            />
            <div className="divide-y divide-gray-200">
              {recentDocuments?.items.length === 0 && (
                <div className="px-6 py-8 text-center text-sm text-gray-500">
                  No documents uploaded yet
                </div>
              )}
              {recentDocuments?.items.map((doc) => (
                <Link
                  key={doc.id}
                  href={`/documents/${doc.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-gray-100 p-2">
                      <Upload className="h-5 w-5 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{doc.original_filename}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant={getStatusVariant(doc.status)}>{doc.status}</Badge>
                </Link>
              ))}
            </div>
          </Card>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary-100 p-3">
                <Building2 className="h-6 w-6 text-primary-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total Vendors</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {entities?.total || 0}
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary-100 p-3">
                <FileCheck className="h-6 w-6 text-primary-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total Requirements</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {summary?.total || 0}
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-success-100 p-3">
                <TrendingUp className="h-6 w-6 text-success-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Compliance Rate</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {summary && summary.total > 0
                    ? Math.round((summary.compliant / summary.total) * 100)
                    : 0}
                  %
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
