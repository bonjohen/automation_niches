import Link from 'next/link'
import {
  Shield,
  FileText,
  Bell,
  Building,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-semibold text-gray-900">
                Compliance Platform
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/login"
                className="text-gray-600 hover:text-gray-900"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="btn btn-primary btn-md"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
              Compliance Management
              <span className="block text-primary-600">Made Simple</span>
            </h1>
            <p className="mt-6 max-w-2xl mx-auto text-xl text-gray-500">
              Automate vendor COI tracking, document processing, and compliance
              monitoring. Never miss an expiration date again.
            </p>
            <div className="mt-10 flex justify-center gap-4">
              <Link href="/register" className="btn btn-primary btn-lg">
                Start Free Trial
              </Link>
              <Link href="/demo" className="btn btn-secondary btn-lg">
                View Demo
              </Link>
            </div>
          </div>

          {/* Features Grid */}
          <div className="mt-24 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<FileText className="h-8 w-8" />}
              title="AI Document Processing"
              description="Upload COIs and let AI automatically extract key information like coverage limits and expiration dates."
            />
            <FeatureCard
              icon={<Bell className="h-8 w-8" />}
              title="Smart Notifications"
              description="Get automated reminders before certificates expire. Customize alert timing for your workflow."
            />
            <FeatureCard
              icon={<Building className="h-8 w-8" />}
              title="Vendor Management"
              description="Track all your vendors in one place. Monitor compliance status at a glance."
            />
            <FeatureCard
              icon={<CheckCircle className="h-8 w-8" />}
              title="Compliance Dashboard"
              description="See your compliance status in real-time. Identify issues before they become problems."
            />
            <FeatureCard
              icon={<AlertTriangle className="h-8 w-8" />}
              title="Risk Assessment"
              description="Categorize vendors by risk level. Prioritize high-risk compliance items."
            />
            <FeatureCard
              icon={<Shield className="h-8 w-8" />}
              title="White-Label Ready"
              description="Customize with your branding. Perfect for property managers and compliance consultants."
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Shield className="h-6 w-6 text-gray-400" />
              <span className="ml-2 text-gray-500">
                © 2024 Compliance Platform
              </span>
            </div>
            <div className="flex space-x-6">
              <a href="#" className="text-gray-500 hover:text-gray-900">
                Privacy
              </a>
              <a href="#" className="text-gray-500 hover:text-gray-900">
                Terms
              </a>
              <a href="#" className="text-gray-500 hover:text-gray-900">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="card p-6">
      <div className="text-primary-600">{icon}</div>
      <h3 className="mt-4 text-lg font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-gray-500">{description}</p>
    </div>
  )
}
