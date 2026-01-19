import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

// API client configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Type definitions
export interface User {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  role: string
  account_id: string
  is_active: boolean
  created_at: string
}

export interface Entity {
  id: string
  account_id: string
  entity_type_id: string
  name: string
  description: string | null
  email: string | null
  phone: string | null
  address: string | null
  status: string
  custom_fields: Record<string, unknown>
  tags: string[]
  created_at: string
  updated_at: string
}

export interface Requirement {
  id: string
  account_id: string
  entity_id: string
  requirement_type_id: string
  name: string
  description: string | null
  due_date: string | null
  status: string
  priority: string
  document_id: string | null
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  account_id: string
  entity_id: string | null
  document_type_id: string | null
  filename: string
  original_filename: string
  mime_type: string
  file_size: number
  status: string
  extracted_data: Record<string, unknown>
  extraction_confidence: number | null
  created_at: string
  updated_at: string
}

export interface Notification {
  id: string
  notification_type: string
  subject: string
  body: string
  status: string
  scheduled_at: string
  read_at: string | null
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ComplianceSummary {
  total: number
  compliant: number
  expiring_soon: number
  expired: number
  pending: number
}

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password })
    return response.data
  },

  register: async (data: {
    email: string
    password: string
    first_name?: string
    last_name?: string
    account_name: string
  }) => {
    const response = await apiClient.post('/auth/register', data)
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}

// Entities API
export const entitiesApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    entity_type_id?: string
    status?: string
    search?: string
  }): Promise<PaginatedResponse<Entity>> => {
    const response = await apiClient.get('/entities', { params })
    return response.data
  },

  get: async (id: string): Promise<Entity> => {
    const response = await apiClient.get(`/entities/${id}`)
    return response.data
  },

  create: async (data: Partial<Entity>): Promise<Entity> => {
    const response = await apiClient.post('/entities', data)
    return response.data
  },

  update: async (id: string, data: Partial<Entity>): Promise<Entity> => {
    const response = await apiClient.patch(`/entities/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/entities/${id}`)
  },

  getTypes: async () => {
    const response = await apiClient.get('/entities/types')
    return response.data
  },
}

// Requirements API
export const requirementsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    entity_id?: string
    status?: string
    priority?: string
    due_before?: string
    due_after?: string
  }): Promise<PaginatedResponse<Requirement>> => {
    const response = await apiClient.get('/requirements', { params })
    return response.data
  },

  get: async (id: string): Promise<Requirement> => {
    const response = await apiClient.get(`/requirements/${id}`)
    return response.data
  },

  create: async (data: Partial<Requirement>): Promise<Requirement> => {
    const response = await apiClient.post('/requirements', data)
    return response.data
  },

  update: async (id: string, data: Partial<Requirement>): Promise<Requirement> => {
    const response = await apiClient.patch(`/requirements/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/requirements/${id}`)
  },

  complete: async (id: string): Promise<Requirement> => {
    const response = await apiClient.post(`/requirements/${id}/complete`)
    return response.data
  },

  getSummary: async (entityId?: string): Promise<ComplianceSummary> => {
    const response = await apiClient.get('/requirements/summary', {
      params: entityId ? { entity_id: entityId } : undefined,
    })
    return response.data
  },

  getTypes: async () => {
    const response = await apiClient.get('/requirements/types')
    return response.data
  },
}

// Documents API
export const documentsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    entity_id?: string
    document_type_id?: string
    status?: string
  }): Promise<PaginatedResponse<Document>> => {
    const response = await apiClient.get('/documents', { params })
    return response.data
  },

  get: async (id: string): Promise<Document> => {
    const response = await apiClient.get(`/documents/${id}`)
    return response.data
  },

  upload: async (
    file: File,
    entityId?: string,
    documentTypeId?: string
  ): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    if (entityId) formData.append('entity_id', entityId)
    if (documentTypeId) formData.append('document_type_id', documentTypeId)

    const response = await apiClient.post('/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  update: async (id: string, data: Partial<Document>): Promise<Document> => {
    const response = await apiClient.patch(`/documents/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`)
  },

  process: async (id: string): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/process`)
    return response.data
  },

  getTypes: async () => {
    const response = await apiClient.get('/documents/types')
    return response.data
  },
}

// Notifications API
export const notificationsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    notification_type?: string
    status?: string
    unread_only?: boolean
  }): Promise<PaginatedResponse<Notification> & { unread_count: number }> => {
    const response = await apiClient.get('/notifications', { params })
    return response.data
  },

  get: async (id: string): Promise<Notification> => {
    const response = await apiClient.get(`/notifications/${id}`)
    return response.data
  },

  markRead: async (id: string): Promise<Notification> => {
    const response = await apiClient.post(`/notifications/${id}/read`)
    return response.data
  },

  markAllRead: async (): Promise<void> => {
    await apiClient.post('/notifications/mark-all-read')
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/notifications/${id}`)
  },
}

export default apiClient
