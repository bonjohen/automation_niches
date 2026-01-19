import { clsx } from 'clsx'

export interface BadgeProps {
  variant?: 'success' | 'warning' | 'danger' | 'gray' | 'primary'
  children: React.ReactNode
  className?: string
}

const variantStyles = {
  success: 'bg-success-50 text-success-600',
  warning: 'bg-warning-50 text-warning-600',
  danger: 'bg-danger-50 text-danger-600',
  gray: 'bg-gray-100 text-gray-600',
  primary: 'bg-primary-50 text-primary-600',
}

export function Badge({ variant = 'gray', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

// Helper function to get badge variant from status
export function getStatusVariant(
  status: string
): 'success' | 'warning' | 'danger' | 'gray' {
  const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'gray'> = {
    compliant: 'success',
    active: 'success',
    processed: 'success',
    sent: 'success',
    read: 'success',

    expiring_soon: 'warning',
    pending: 'warning',
    in_progress: 'warning',
    processing: 'warning',
    needs_review: 'warning',

    expired: 'danger',
    non_compliant: 'danger',
    failed: 'danger',
    overdue: 'danger',

    inactive: 'gray',
    archived: 'gray',
    cancelled: 'gray',
  }

  return statusMap[status] || 'gray'
}
