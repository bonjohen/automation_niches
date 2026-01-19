'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { ArrowLeft, CheckCircle, XCircle, Loader2, Copy, Check, ExternalLink } from 'lucide-react'
import { AuthenticatedLayout } from '@/components/layout'
import { Card, CardHeader, Button, Input, Badge } from '@/components/ui'
import { integrationsApi } from '@/services/api'

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="text-gray-400 hover:text-gray-600 transition-colors"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-4 w-4 text-success-500" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </button>
  )
}

export default function ZapierSettingsPage() {
  const queryClient = useQueryClient()
  const [entityCreatedUrl, setEntityCreatedUrl] = useState('')
  const [entityUpdatedUrl, setEntityUpdatedUrl] = useState('')
  const [complianceChangedUrl, setComplianceChangedUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  const { data: settings, isLoading } = useQuery({
    queryKey: ['integration-settings'],
    queryFn: integrationsApi.getSettings,
    onSuccess: (data) => {
      if (data.zapier) {
        setEntityCreatedUrl(data.zapier.webhook_url_entity_created || '')
        setEntityUpdatedUrl(data.zapier.webhook_url_entity_updated || '')
        setComplianceChangedUrl(data.zapier.webhook_url_compliance_changed || '')
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

  const handleSave = () => {
    updateMutation.mutate({
      provider: 'zapier',
      enabled: true,
      zapier: {
        webhook_url_entity_created: entityCreatedUrl || undefined,
        webhook_url_entity_updated: entityUpdatedUrl || undefined,
        webhook_url_compliance_changed: complianceChangedUrl || undefined,
        ...(webhookSecret && !webhookSecret.startsWith('*') ? { webhook_secret: webhookSecret } : {}),
      },
    })
  }

  const handleDisconnect = () => {
    updateMutation.mutate({
      provider: 'none',
      enabled: false,
      zapier: {
        webhook_url_entity_created: '',
        webhook_url_entity_updated: '',
        webhook_url_compliance_changed: '',
        webhook_secret: '',
      },
    })
    setEntityCreatedUrl('')
    setEntityUpdatedUrl('')
    setComplianceChangedUrl('')
    setWebhookSecret('')
    setTestResult(null)
  }

  const isConnected = settings?.provider === 'zapier' && (
    settings?.zapier?.webhook_url_entity_created ||
    settings?.zapier?.webhook_url_compliance_changed
  )

  const inboundWebhookUrl = settings?.zapier?.inbound_webhook_url || ''

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
            <h1 className="text-2xl font-bold text-gray-900">Zapier Integration</h1>
            <p className="mt-1 text-sm text-gray-600">
              Connect to any CRM via Zapier webhooks.
            </p>
          </div>
        </div>

        {/* Connection Status */}
        <Card>
          <CardHeader
            title="Connection Status"
            description="Current Zapier webhook configuration."
          />
          <div className="px-6 pb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isConnected ? (
                  <>
                    <CheckCircle className="h-8 w-8 text-success-500" />
                    <div>
                      <p className="font-medium text-gray-900">Configured</p>
                      <p className="text-sm text-gray-500">
                        Webhooks will be sent when events occur.
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <XCircle className="h-8 w-8 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">Not Configured</p>
                      <p className="text-sm text-gray-500">
                        Enter your Zapier webhook URLs below.
                      </p>
                    </div>
                  </>
                )}
              </div>

              {isConnected && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => testMutation.mutate()}
                  disabled={testMutation.isPending}
                >
                  {testMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Test Webhook'
                  )}
                </Button>
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
          </div>
        </Card>

        {/* Outbound Webhooks */}
        <Card>
          <CardHeader
            title="Outbound Webhooks (Our Platform -> Zapier)"
            description="Enter your Zapier webhook URLs to receive events from this platform."
          />
          <div className="px-6 pb-6 space-y-4">
            <div>
              <label htmlFor="entityCreatedUrl" className="block text-sm font-medium text-gray-700">
                Vendor Created Webhook
              </label>
              <Input
                id="entityCreatedUrl"
                value={entityCreatedUrl}
                onChange={(e) => setEntityCreatedUrl(e.target.value)}
                placeholder="https://hooks.zapier.com/hooks/catch/..."
                className="mt-1"
              />
              <p className="mt-1 text-xs text-gray-500">
                Triggered when a new vendor is added.
              </p>
            </div>

            <div>
              <label htmlFor="entityUpdatedUrl" className="block text-sm font-medium text-gray-700">
                Vendor Updated Webhook
              </label>
              <Input
                id="entityUpdatedUrl"
                value={entityUpdatedUrl}
                onChange={(e) => setEntityUpdatedUrl(e.target.value)}
                placeholder="https://hooks.zapier.com/hooks/catch/..."
                className="mt-1"
              />
              <p className="mt-1 text-xs text-gray-500">
                Triggered when vendor details are updated.
              </p>
            </div>

            <div>
              <label htmlFor="complianceChangedUrl" className="block text-sm font-medium text-gray-700">
                Compliance Changed Webhook
              </label>
              <Input
                id="complianceChangedUrl"
                value={complianceChangedUrl}
                onChange={(e) => setComplianceChangedUrl(e.target.value)}
                placeholder="https://hooks.zapier.com/hooks/catch/..."
                className="mt-1"
              />
              <p className="mt-1 text-xs text-gray-500">
                Triggered when compliance status changes (hourly sync).
              </p>
            </div>
          </div>
        </Card>

        {/* Inbound Webhook */}
        <Card>
          <CardHeader
            title="Inbound Webhook (Zapier -> Our Platform)"
            description="Use this URL in your Zapier action to send updates back to this platform."
          />
          <div className="px-6 pb-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Your Inbound Webhook URL
              </label>
              <div className="mt-1 flex items-center gap-2">
                <Input
                  value={inboundWebhookUrl}
                  readOnly
                  className="font-mono text-sm bg-gray-50"
                />
                {inboundWebhookUrl && <CopyButton text={inboundWebhookUrl} />}
              </div>
              <p className="mt-1 text-xs text-gray-500">
                POST JSON data to this URL to update vendors in this platform.
              </p>
            </div>

            <div>
              <label htmlFor="webhookSecret" className="block text-sm font-medium text-gray-700">
                Webhook Secret (Optional)
              </label>
              <Input
                id="webhookSecret"
                type="password"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
                placeholder={settings?.zapier?.webhook_secret ? '••••••••' : 'Enter a secret for HMAC validation'}
                className="mt-1"
              />
              <p className="mt-1 text-xs text-gray-500">
                Add an X-Webhook-Signature header with HMAC-SHA256 signature to validate inbound webhooks.
              </p>
            </div>
          </div>
        </Card>

        {/* Payload Format */}
        <Card>
          <CardHeader
            title="Webhook Payload Format"
            description="Expected format for inbound webhook requests."
          />
          <div className="px-6 pb-6">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
{`{
  "event": "contact.created" | "contact.updated",
  "external_id": "crm-record-id-123",
  "data": {
    "name": "Vendor Name",
    "email": "vendor@example.com",
    "phone": "+1-555-0100",
    "address": "123 Main St"
  }
}`}
            </pre>
          </div>
        </Card>

        {/* Help Link */}
        <Card>
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Need help setting up Zapier?</p>
              <p className="text-sm text-gray-600">
                Check our guide on creating Zapier workflows.
              </p>
            </div>
            <a
              href="https://zapier.com/help/create/basics/create-zaps"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Zapier Documentation
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex justify-between">
          {isConnected && (
            <Button variant="danger" onClick={handleDisconnect}>
              Disconnect Zapier
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
              {isConnected ? 'Update Settings' : 'Save Configuration'}
            </Button>
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  )
}
