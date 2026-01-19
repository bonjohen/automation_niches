'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, entitiesApi } from '@/services/api'
import { AuthenticatedLayout } from '@/components/layout'
import { Button, Card, CardHeader } from '@/components/ui'
import {
  ArrowLeft,
  Upload,
  FileText,
  X,
  Loader2,
  AlertCircle,
  CheckCircle,
  File,
  FileImage,
} from 'lucide-react'

const acceptedTypes = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/tiff',
]

const documentTypes = [
  { value: '', label: 'Auto-detect' },
  { value: 'certificate_of_insurance', label: 'Certificate of Insurance (COI)' },
  { value: 'workers_comp_certificate', label: 'Workers Compensation Certificate' },
]

interface UploadedFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  documentId?: string
}

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

export default function DocumentUploadPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const queryClient = useQueryClient()

  const entityIdParam = searchParams.get('entity_id')
  const [entityId, setEntityId] = useState(entityIdParam || '')
  const [documentTypeId, setDocumentTypeId] = useState('')
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [autoProcess, setAutoProcess] = useState(true)

  // Fetch entities for dropdown
  const { data: entities } = useQuery({
    queryKey: ['entities'],
    queryFn: () => entitiesApi.list({ page_size: 100 }),
  })

  const uploadMutation = useMutation({
    mutationFn: async (uploadFile: UploadedFile) => {
      const doc = await documentsApi.upload(
        uploadFile.file,
        entityId || undefined,
        documentTypeId || undefined
      )
      if (autoProcess) {
        await documentsApi.process(doc.id)
      }
      return doc
    },
  })

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFiles = Array.from(e.dataTransfer.files).filter((file) =>
      acceptedTypes.includes(file.type)
    )

    addFiles(droppedFiles)
  }, [])

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const selectedFiles = Array.from(e.target.files).filter((file) =>
          acceptedTypes.includes(file.type)
        )
        addFiles(selectedFiles)
      }
    },
    []
  )

  const addFiles = (newFiles: File[]) => {
    const newUploadFiles: UploadedFile[] = newFiles.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      status: 'pending',
    }))
    setFiles((prev) => [...prev, ...newUploadFiles])
  }

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
  }

  const uploadFile = async (uploadFile: UploadedFile) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
      )
    )

    try {
      const doc = await uploadMutation.mutateAsync(uploadFile)
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: 'success', documentId: doc.id }
            : f
        )
      )
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? {
                ...f,
                status: 'error',
                error: (error as Error).message || 'Upload failed',
              }
            : f
        )
      )
    }
  }

  const uploadAllPending = async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending')
    for (const file of pendingFiles) {
      await uploadFile(file)
    }
  }

  const pendingCount = files.filter((f) => f.status === 'pending').length
  const uploadingCount = files.filter((f) => f.status === 'uploading').length
  const successCount = files.filter((f) => f.status === 'success').length
  const errorCount = files.filter((f) => f.status === 'error').length

  const allDone =
    files.length > 0 && pendingCount === 0 && uploadingCount === 0

  return (
    <AuthenticatedLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/documents" className="p-2 rounded-lg hover:bg-gray-100">
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Upload Documents</h1>
            <p className="text-gray-500 mt-1">
              Upload certificates of insurance or other compliance documents
            </p>
          </div>
        </div>

        {/* Upload Settings */}
        <Card>
          <CardHeader
            title="Upload Settings"
            description="Configure how documents will be processed"
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Associate with Vendor
              </label>
              <select
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                className="block w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="">No vendor selected</option>
                {entities?.items.map((entity) => (
                  <option key={entity.id} value={entity.id}>
                    {entity.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Document Type
              </label>
              <select
                value={documentTypeId}
                onChange={(e) => setDocumentTypeId(e.target.value)}
                className="block w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm focus:border-primary-500 focus:ring-primary-500"
              >
                {documentTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={autoProcess}
                  onChange={(e) => setAutoProcess(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">
                  Automatically process documents after upload (extract data using AI)
                </span>
              </label>
            </div>
          </div>
        </Card>

        {/* Upload Zone */}
        <Card padding="none">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`p-8 border-2 border-dashed rounded-lg m-6 transition-colors ${
              isDragging
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="flex flex-col items-center justify-center text-center">
              <Upload
                className={`h-12 w-12 mb-4 ${
                  isDragging ? 'text-primary-500' : 'text-gray-400'
                }`}
              />
              <p className="text-lg font-medium text-gray-900">
                {isDragging
                  ? 'Drop files here'
                  : 'Drag and drop files here, or click to browse'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Supported formats: PDF, PNG, JPEG, TIFF
              </p>
              <label className="mt-4">
                <input
                  type="file"
                  multiple
                  accept={acceptedTypes.join(',')}
                  onChange={handleFileSelect}
                  className="sr-only"
                />
                <span className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                  Browse Files
                </span>
              </label>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="border-t border-gray-200">
              <div className="px-6 py-4 bg-gray-50 flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  {files.length} file{files.length !== 1 ? 's' : ''} selected
                  {successCount > 0 && (
                    <span className="ml-2 text-success-600">
                      ({successCount} uploaded)
                    </span>
                  )}
                  {errorCount > 0 && (
                    <span className="ml-2 text-danger-600">
                      ({errorCount} failed)
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setFiles([])}
                    disabled={uploadingCount > 0}
                  >
                    Clear All
                  </Button>
                  <Button
                    size="sm"
                    onClick={uploadAllPending}
                    disabled={pendingCount === 0 || uploadingCount > 0}
                  >
                    {uploadingCount > 0 ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload All ({pendingCount})
                      </>
                    )}
                  </Button>
                </div>
              </div>
              <ul className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {files.map((uploadFile) => {
                  const FileIcon = getFileIcon(uploadFile.file.type)
                  return (
                    <li
                      key={uploadFile.id}
                      className="px-6 py-4 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="h-10 w-10 flex-shrink-0 bg-gray-100 rounded-lg flex items-center justify-center">
                          <FileIcon className="h-5 w-5 text-gray-500" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {uploadFile.file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(uploadFile.file.size)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 ml-4">
                        {uploadFile.status === 'pending' && (
                          <>
                            <span className="text-xs text-gray-500">Ready</span>
                            <button
                              onClick={() => removeFile(uploadFile.id)}
                              className="p-1 rounded hover:bg-gray-100"
                            >
                              <X className="h-4 w-4 text-gray-400" />
                            </button>
                          </>
                        )}
                        {uploadFile.status === 'uploading' && (
                          <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
                        )}
                        {uploadFile.status === 'success' && (
                          <>
                            <CheckCircle className="h-5 w-5 text-success-500" />
                            {uploadFile.documentId && (
                              <Link
                                href={`/documents/${uploadFile.documentId}`}
                                className="text-xs text-primary-600 hover:underline"
                              >
                                View
                              </Link>
                            )}
                          </>
                        )}
                        {uploadFile.status === 'error' && (
                          <>
                            <div className="flex items-center gap-2">
                              <AlertCircle className="h-5 w-5 text-danger-500" />
                              <span className="text-xs text-danger-600">
                                {uploadFile.error}
                              </span>
                            </div>
                            <button
                              onClick={() => uploadFile && uploadFile.status === 'error' && setFiles(prev => prev.map(f => f.id === uploadFile.id ? {...f, status: 'pending', error: undefined} : f))}
                              className="text-xs text-primary-600 hover:underline"
                            >
                              Retry
                            </button>
                          </>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </Card>

        {/* Success Message */}
        {allDone && successCount > 0 && (
          <Card className="bg-success-50 border-success-200">
            <div className="flex items-center gap-4">
              <CheckCircle className="h-8 w-8 text-success-500" />
              <div>
                <h3 className="text-lg font-medium text-success-800">
                  Upload Complete
                </h3>
                <p className="text-success-600">
                  {successCount} document{successCount !== 1 ? 's' : ''}{' '}
                  {successCount !== 1 ? 'have' : 'has'} been uploaded
                  {autoProcess ? ' and sent for processing' : ''}.
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-3">
              <Link href="/documents">
                <Button>View All Documents</Button>
              </Link>
              <Button
                variant="outline"
                onClick={() => setFiles([])}
              >
                Upload More
              </Button>
            </div>
          </Card>
        )}
      </div>
    </AuthenticatedLayout>
  )
}
