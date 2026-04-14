'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const SAMPLE_URLS = [
  {
    name: 'Laundry Sauce',
    organization_id: 'laundrysauce.com',
    description: 'Bold, soulful fragrances in simple-to-use, performance pods.',
  },
]

export default function HomePage() {
  const router = useRouter()
  const [organizationId, setOrganizationId] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    let id = organizationId.trim()
    // Strip protocol, www, paths, and trailing slashes from pasted URLs
    id = id.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].split('?')[0]
    if (!id) {
      setError('Please enter an organization ID or domain')
      return
    }
    router.push(`/company-status?organization_id=${encodeURIComponent(id)}`)
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4 sm:p-6">
      <div className="max-w-xl w-full">
        <h1 className="text-4xl font-bold text-white text-center mb-2">
          Company Pulse
        </h1>
        <p className="text-center text-white/50 mb-8">
          Real-time company status reports from Day AI, HubSpot, Luma &amp; StoreLeads
        </p>

        {/* Input Section */}
        <div className="glass-panel rounded-2xl p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="orgId" className="block text-sm text-white/60 mb-1">
                Organization Domain
              </label>
              <input
                id="orgId"
                type="text"
                value={organizationId}
                onChange={(e) => setOrganizationId(e.target.value)}
                placeholder="e.g. laundrysauce.com"
                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-colors"
              />
              {error && (
                <p className="text-red-400 text-xs mt-1">{error}</p>
              )}
            </div>
            <button
              type="submit"
              className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
            >
              Get Company Status
            </button>
          </form>
        </div>

        {/* Sample Companies */}
        {SAMPLE_URLS.length > 0 && (
          <div>
            <h2 className="text-sm text-white/40 mb-3">Sample Companies</h2>
            <div className="grid gap-3">
              {SAMPLE_URLS.map((sample) => (
                <button
                  key={sample.organization_id}
                  onClick={() =>
                    router.push(
                      `/company-status?organization_id=${encodeURIComponent(sample.organization_id)}`
                    )
                  }
                  className="glass-panel rounded-xl p-4 text-left hover:bg-white/[0.06] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-white">{sample.name}</h3>
                      <p className="text-xs text-white/50 mt-0.5">{sample.description}</p>
                      <p className="text-xs text-white/30 mt-1 font-mono">{sample.organization_id}</p>
                    </div>
                    <span className="text-white/30 text-lg">→</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8 text-center text-xs text-white/30">
          Powered by{' '}
          <a
            href="https://day.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="text-white/50 hover:text-white/70 transition-colors"
          >
            Day AI
          </a>
        </div>
      </div>
    </main>
  )
}
