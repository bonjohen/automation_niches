'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { ArrowLeft, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react'
import { AuthenticatedLayout } from '@/components/layout'
import { Card, CardHeader, Button, Input, Badge } from '@/components/ui'
import { integrationsApi } from '@/services/api'

export default function HubSpotSettingsPage() {
  const queryClient = useQueryClient()
  const [apiKey, setApiKey] = useState('')
  const [portalId, setPortalId] = useState('')
  const [objectType, setObjectType] = useState('companies')
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  const { data: settings, isLoading } = useQuery({
    queryKey: ['integration-settings'],
    queryFn: integrationsApi.getSettings,
    onSuccess: (data) => {
      if (data.hubspot) {
        setPortalId(data.hubspot.portal_id || '')
        setObjectType(data.hubspot.object_type || 'companies')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: integrationsApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-settings'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: integrationsApi.testConnection,
    onSuccess: (result) => {
      setTestResult(result)
    },
  })

  const syncMutation = useMutation({
    mutationFn: () => integrationsApi.pushToCRM(),
  })

  const handleSave = () => {
    updateMutation.mutate({
      provider: 'hubspot',
      enabled: true,
      hubspot: {
        ...(apiKey && !apiKey.startsWith('*') ? { api_key: apiKey } : {}),
        portal_id: portalId,
        object_type: objectType,
      },
    })
  }

  const handleDisconnect = () => {
    updateMutation.mutate({
      provider: 'none',
      enabled: false,
      hubspot: {
        api_key: '',
      },
    })
    setApiKey('')
    setTestResult(null)
  }

  const isConnected = settings?.provider === 'hubspot' && settings?.hubspot?.has_credentials

  return (
    <AuthenticatedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/settings/integrations">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">HubSpot Integration</h1>
            <p className="mt-1 text-sm text-gray-600">
              Connect your HubSpot account to sync vendors and compliance status.
            </p>
          </div>
        </div>

        {/* Connection Status */}
        <Card>
          <CardHeader
            title="Connection Status"
            description="Current connection status to HubSpot."
          />
          <div className="px-6 pb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isConnected ? (
                  <>
                    <CheckCircle className="h-8 w-8 text-success-500" />
                    <div>
                      <p className="font-medium text-gray-900">Connected</p>
                      <p className="text-sm text-gray-500">
                        Portal ID: {settings?.hubspot?.portal_id || 'Not set'}
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <XCircle className="h-8 w-8 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">Not Connected</p>
                      <p className="text-sm text-gray-500">
                        Enter your API key below to connect.
                      </p>
                    </div>
                  </>
                )}
              </div>

              {isConnected && (
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => testMutation.mutate()}
                    disabled={testMutation.isPending}
                  >
                    {testMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Test Connection'
                    )}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => syncMutation.mutate()}
                    disabled={syncMutation.isPending}
                  >
                    {syncMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    Sync Now
                  </Button>
                </div>
              )}
            </div>

            {/* Test Result */}
            {testResult && (
              <div className={`mt-4 rounded-md p-4 ${testResult.success ? 'bg-success-50' : 'bg-danger-50'}`}>
                <div className="flex items-center gap-2">
                  {testResult.success ? (
                    <CheckCircle className="h-5 w-5 text-success-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-danger-500" />
                  )}
                  <p className={testResult.success ? 'text-success-700' : 'text-danger-700'}>
                    {testResult.message}
                  </p>
                </div>
              </div>
            )}

            {/* Sync Result */}
            {syncMutation.isSuccess && (
              <div className="mt-4 rounded-md bg-success-50 p-4">
                <p className="text-success-700">
                  Sync complete: {syncMutation.data?.synced_count} synced, {syncMutation.data?.failed_count} failed
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader
            title="API Configuration"
            description="Enter your HubSpot private app API key to connect."
          />
          <div className="px-6 pb-6 space-y-4">
            <div>
              <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700">
                API Key
              </label>
              <Input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={isConnected ? '••••••••' : 'pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}
                className="mt-1"
              />
              <p className="mt-1 text-xs text-gray-500">
                Create a private app in HubSpot to get your API key.{' '}
                <a
                  href="https://developers.hubspot.com/docs/api/private-apps"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  Learn more
                </a>
              </p>
            </div>

            <div>
              <label htmlFor="portalId" className="block text-sm font-medium text-gray-700">
                Portal ID (Optional)
              </label>
              <Input
                id="portalId"
                value={portalId}
                onChange={(e) => setPortalId(e.target.value)}
                placeholder="12345678"
                className="mt-1"
              />
              <p className="mt-1 text-xs text-gray-500">
                Your HubSpot portal ID. Found in your HubSpot URL.
              </p>
            </div>

            <div>
              <label htmlFor="objectType" className="block text-sm font-medium text-gray-700">
                Sync To
              </label>
              <select
                id="objectType"
                value={objectType}
                onChange={(e) => setObjectType(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="companies">Companies</option>
                <option value="contacts">Contacts</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Choose whether to sync vendors as Companies or Contacts in HubSpot.
              </p>
            </div>
          </div>
        </Card>

        {/* Required HubSpot Properties */}
        <Card>
          <CardHeader
            title="Required HubSpot Properties"
            description="Create these custom properties in HubSpot to receive compliance data."
          />
          <div className="px-6 pb-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Property Name</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr>
                    <td className="px-4 py-3 text-sm font-mono text-gray-900">compliance_status</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Single-line text</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Compliance status (compliant, expiring_soon, expired)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm font-mono text-gray-900">compliance_expiry</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Date</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Next compliance document expiration date</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm font-mono text-gray-900">compliance_last_updated</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Date & time</td>
                    <td className="px-4 py-3 text-sm text-gray-600">When compliance status was last synced</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex justify-between">
          {isConnected && (
            <Button variant="danger" onClick={handleDisconnect}>
              Disconnect HubSpot
            </Button>
          )}
          <div className="flex gap-2 ml-auto">
            <Link href="/settings/integrations">
              <Button variant="secondary">Cancel</Button>
            </Link>
            <Button
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {isConnected ? 'Update Settings' : 'Connect HubSpot'}
            </Button>
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
