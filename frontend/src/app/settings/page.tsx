'use client'

import Link from 'next/link'
import { Settings, Link2, Bell, Building2, Users } from 'lucide-react'
import { AuthenticatedLayout } from '@/components/layout'
import { Card, CardHeader } from '@/components/ui'

interface SettingsCardProps {
  title: string
  description: string
  href: string
  icon: React.ElementType
}

function SettingsCard({ title, description, href, icon: Icon }: SettingsCardProps) {
  return (
    <Link href={href}>
      <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className="rounded-lg bg-primary-100 p-3">
              <Icon className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <p className="mt-1 text-sm text-gray-600">{description}</p>
            </div>
          </div>
        </div>
      </Card>
    </Link>
  )
}

export default function SettingsPage() {
  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="mt-1 text-sm text-gray-600">
            Configure your account, integrations, and preferences.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <SettingsCard
            title="Integrations"
            description="Connect your CRM and other tools to sync vendor data automatically."
            href="/settings/integrations"
            icon={Link2}
          />

          <SettingsCard
            title="Notifications"
            description="Configure how and when you receive compliance alerts."
            href="/settings/notifications"
            icon={Bell}
          />

          <SettingsCard
            title="Account"
            description="Manage your organization details and branding."
            href="/settings/account"
            icon={Building2}
          />

          <SettingsCard
            title="Team"
            description="Invite team members and manage permissions."
            href="/settings/team"
            icon={Users}
          />
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
