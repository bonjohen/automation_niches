'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { CheckCircle, XCircle, Clock, Link2, ArrowRight } from 'lucide-react'
import { AuthenticatedLayout } from '@/components/layout'
import { Card, CardHeader, Badge, Button } from '@/components/ui'
import { integrationsApi } from '@/services/api'

function ConnectionStatus({ connected, lastSync }: { connected: boolean; lastSync?: string | null }) {
  if (connected) {
    return (
      <div className="flex items-center gap-2">
        <CheckCircle className="h-5 w-5 text-success-500" />
        <span className="text-sm text-success-600">Connected</span>
        {lastSync && (
          <span className="text-xs text-gray-500">
            Last sync: {new Date(lastSync).toLocaleDateString()}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <XCircle className="h-5 w-5 text-gray-400" />
      <span className="text-sm text-gray-600">Not connected</span>
    </div>
  )
}

interface IntegrationCardProps {
  name: string
  description: string
  logo: string
  connected: boolean
  href: string
  lastSync?: string | null
}

function IntegrationCard({ name, description, logo, connected, href, lastSync }: IntegrationCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-lg bg-gray-100 flex items-center justify-center text-2xl">
              {logo}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{name}</h3>
              <p className="mt-1 text-sm text-gray-600">{description}</p>
              <div className="mt-3">
                <ConnectionStatus connected={connected} lastSync={lastSync} />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Link href={href}>
            <Button variant="secondary" size="sm">
              {connected ? 'Configure' : 'Connect'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  )
}

export default function IntegrationsPage() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['integration-settings'],
    queryFn: integrationsApi.getSettings,
  })

  const hubspotConnected = settings?.provider === 'hubspot' && settings?.hubspot?.has_credentials
  const zapierConnected = settings?.provider === 'zapier' && (
    settings?.zapier?.webhook_url_entity_created ||
    settings?.zapier?.webhook_url_compliance_changed
  )

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
            <p className="mt-1 text-sm text-gray-600">
              Connect your CRM to automatically sync vendor data and compliance status.
            </p>
          </div>
          <Link href="/settings/sync-history">
            <Button variant="secondary">
              <Clock className="mr-2 h-4 w-4" />
              Sync History
            </Button>
          </Link>
        </div>

        {/* Quick Status */}
        {settings && (settings.provider || settings.last_sync_at) && (
          <Card>
            <div className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link2 className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {settings.provider ? `Connected to ${settings.provider}` : 'No integration active'}
                  </p>
                  {settings.last_sync_at && (
                    <p className="text-xs text-gray-500">
                      Last sync: {new Date(settings.last_sync_at).toLocaleString()} -
                      Status: <span className={settings.last_sync_status === 'success' ? 'text-success-600' : 'text-warning-600'}>
                        {settings.last_sync_status}
                      </span>
                    </p>
                  )}
                </div>
              </div>
              {settings.enabled && (
                <Badge variant={settings.last_sync_status === 'success' ? 'success' : 'warning'}>
                  {settings.enabled ? 'Active' : 'Disabled'}
                </Badge>
              )}
            </div>
          </Card>
        )}

        {/* Integration Cards */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <IntegrationCard
            name="HubSpot"
            description="Sync vendors with HubSpot contacts or companies. Push compliance status as custom properties."
            logo="H"
            connected={!!hubspotConnected}
            href="/settings/integrations/hubspot"
            lastSync={hubspotConnected ? settings?.last_sync_at : null}
          />

          <IntegrationCard
            name="Zapier"
            description="Connect to any CRM via Zapier webhooks. Send vendor and compliance updates to 5000+ apps."
            logo="Z"
            connected={!!zapierConnected}
            href="/settings/integrations/zapier"
            lastSync={zapierConnected ? settings?.last_sync_at : null}
          />
        </div>

        {/* Info Section */}
        <Card>
          <CardHeader
            title="How Integrations Work"
            description="Understand how data flows between your compliance platform and CRM."
          />
          <div className="px-6 pb-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-lg border border-gray-200 p-4">
                <div className="text-2xl mb-2">1</div>
                <h4 className="font-medium text-gray-900">Connect</h4>
                <p className="mt-1 text-sm text-gray-600">
                  Add your CRM API key or connect via OAuth to enable syncing.
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 p-4">
                <div className="text-2xl mb-2">2</div>
                <h4 className="font-medium text-gray-900">Sync Vendors</h4>
                <p className="mt-1 text-sm text-gray-600">
                  New vendors are automatically created in your CRM when added here.
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 p-4">
                <div className="text-2xl mb-2">3</div>
                <h4 className="font-medium text-gray-900">Track Compliance</h4>
                <p className="mt-1 text-sm text-gray-600">
                  Compliance status is pushed to custom fields, keeping your team informed.
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </AuthenticatedLayout>
  )
}
