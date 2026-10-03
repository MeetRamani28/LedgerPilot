import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingUp,
  Cpu,
  RefreshCw,
} from 'lucide-react'
import { AppShell } from './components/layout/AppShell'
import { useAppDispatch, useAppSelector } from './app/store'
import { setActiveTab } from './features/ui/uiSlice'
import { apiClient } from './lib/api-client'

export default function App() {
  const dispatch = useAppDispatch()
  const activeTab = useAppSelector((state) => state.ui.activeTab)

  // Fetch invoices using TanStack Query
  const { data: invoices, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['invoices'],
    queryFn: async () => {
      try {
        return await apiClient.get<any[]>('/api/v1/invoices/')
      } catch (err: any) {
        console.warn('API fetch warning:', err.message)
        return []
      }
    },
  })

  // Fetch audit logs
  const { data: auditLogs } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      try {
        return await apiClient.get<any[]>('/api/v1/audit-logs/')
      } catch {
        return []
      }
    },
    enabled: activeTab === 'audit',
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            <span>Approved</span>
          </span>
        )
      case 'READY_FOR_REVIEW':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Clock className="h-3 w-3" />
            <span>Ready for Review</span>
          </span>
        )
      case 'EXTRACTING':
      case 'MATCHING':
      case 'ANOMALY_CHECK':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>{status.replace('_', ' ')}</span>
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle className="h-3 w-3" />
            <span>Rejected</span>
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300">
            <span>{status}</span>
          </span>
        )
    }
  }

  return (
    <AppShell>
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Total Invoices</span>
            <FileText className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-semibold text-white">{invoices?.length || 0}</span>
            <span className="text-[11px] text-emerald-400 flex items-center">
              <TrendingUp className="h-3 w-3 mr-0.5" /> Pipeline Active
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Ready for Review</span>
            <Clock className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-semibold text-white">
              {invoices?.filter((i) => i.status === 'READY_FOR_REVIEW').length || 0}
            </span>
            <span className="text-[11px] text-amber-400">Needs AP Signoff</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Reconciled & Approved</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-semibold text-white">
              {invoices?.filter((i) => i.status === 'APPROVED').length || 0}
            </span>
            <span className="text-[11px] text-emerald-400">100% Matched</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Vision Engine</span>
            <Cpu className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-sm font-semibold text-slate-200">Groq LPU Vision</span>
            <span className="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded">
              Llama 3.2
            </span>
          </div>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'invoices' && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-sm">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-base font-medium text-white">Invoices & Reconciliation Queue</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Autonomous 3-way match tracking across purchase orders, line items, and goods receipts.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  refetch()
                  toast.info('Refreshing invoice queue...')
                }}
                disabled={isFetching}
                className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors cursor-pointer"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
              <button
                onClick={() => dispatch(setActiveTab('upload'))}
                className="flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 transition-colors shadow-sm cursor-pointer"
              >
                <UploadCloud className="h-3.5 w-3.5" />
                <span>Upload Invoice</span>
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-slate-500 text-sm">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Loading invoice queue...
            </div>
          ) : !invoices || invoices.length === 0 ? (
            <div className="p-12 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-800/80 text-slate-400 mb-3">
                <FileText className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-medium text-slate-200">No invoices in queue</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Upload your first accounts payable PDF to trigger autonomous vision extraction and 3-way reconciliation.
              </p>
              <button
                onClick={() => dispatch(setActiveTab('upload'))}
                className="mt-4 inline-flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-medium text-white hover:bg-indigo-500 transition-colors cursor-pointer"
              >
                <UploadCloud className="h-3.5 w-3.5" />
                <span>Upload Now</span>
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4 font-medium">Invoice #</th>
                    <th className="py-3 px-4 font-medium">Status</th>
                    <th className="py-3 px-4 font-medium">Total Amount</th>
                    <th className="py-3 px-4 font-medium">Confidence</th>
                    <th className="py-3 px-4 font-medium">Created</th>
                    <th className="py-3 px-4 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-white">
                        {inv.invoice_number || 'PENDING'}
                      </td>
                      <td className="py-3.5 px-4">{getStatusBadge(inv.status)}</td>
                      <td className="py-3.5 px-4 font-mono text-slate-200">
                        {inv.currency || 'USD'} ${inv.total_amount?.toFixed(2) || '0.00'}
                      </td>
                      <td className="py-3.5 px-4">
                        {inv.confidence_score !== null && inv.confidence_score !== undefined ? (
                          <div className="flex items-center space-x-2">
                            <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-1.5 rounded-full ${
                                  inv.confidence_score >= 0.9
                                    ? 'bg-emerald-500'
                                    : inv.confidence_score >= 0.7
                                    ? 'bg-amber-500'
                                    : 'bg-rose-500'
                                }`}
                                style={{ width: `${Math.round(inv.confidence_score * 100)}%` }}
                              />
                            </div>
                            <span className="font-mono text-slate-400 text-[11px]">
                              {Math.round(inv.confidence_score * 100)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-500 text-[11px]">-</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {new Date(inv.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            toast.info(`Opening review for invoice ${inv.invoice_number}`)
                          }}
                          className="inline-flex items-center space-x-1 text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
                        >
                          <span>Review</span>
                          <ArrowRight className="h-3 w-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Upload Launcher View */}
      {activeTab === 'upload' && (
        <div className="max-w-2xl mx-auto rounded-xl border border-slate-800 bg-slate-900/40 p-8 shadow-sm text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 mb-4 border border-indigo-500/20">
            <UploadCloud className="h-7 w-7" />
          </div>
          <h2 className="text-lg font-semibold text-white">Upload Accounts-Payable Invoice</h2>
          <p className="text-xs text-slate-400 mt-1 mb-6 max-w-md mx-auto">
            Autonomous pipeline rasterizes PDF, extracts line items with Groq LPU Vision, and executes 3-way matching.
          </p>

          <div
            onClick={() => {
              toast.info('Step 7 will implement interactive drag & drop and split-screen document viewer.')
            }}
            className="border-2 border-dashed border-slate-700/80 hover:border-indigo-500 transition-colors rounded-xl p-10 cursor-pointer bg-slate-950/40"
          >
            <p className="text-sm font-medium text-slate-200">Drag & drop invoice PDF, or click to browse</p>
            <p className="text-xs text-slate-500 mt-1">Multi-page PDF up to 15MB</p>
          </div>
        </div>
      )}

      {/* Audit Log View */}
      {activeTab === 'audit' && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-sm">
          <h2 className="text-base font-medium text-white mb-2">Audit Trail & Compliance Log</h2>
          <p className="text-xs text-slate-400 mb-4">
            Immutable tracking of state changes, user reviews, and automated reconciliation events.
          </p>
          {!auditLogs || auditLogs.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No audit records recorded yet.</p>
          ) : (
            <div className="space-y-2">
              {auditLogs.map((log: any) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-indigo-400 font-medium">{log.action}</span>
                    <span className="text-slate-300">{log.entity_type} #{log.entity_id.slice(0, 8)}</span>
                  </div>
                  <div className="flex items-center space-x-4 text-slate-500">
                    <span>Actor: {log.actor_type}</span>
                    <span>{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settings / Telemetry View */}
      {activeTab === 'settings' && (
        <div className="max-w-2xl rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-sm space-y-4">
          <h2 className="text-base font-medium text-white">System Telemetry & Provider Architecture</h2>
          <div className="space-y-3 text-xs divide-y divide-slate-800">
            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-400">Database Engine</span>
              <span className="font-mono text-slate-200">SQLite (Local) / Supabase Postgres (Prod)</span>
            </div>
            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-400">Vector Store Provider</span>
              <span className="font-mono text-slate-200">ChromaDB (Local) / Pinecone (Prod)</span>
            </div>
            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-400">Vision Extraction Model</span>
              <span className="font-mono text-slate-200">Groq LPU Vision (Llama 3.2 11B)</span>
            </div>
            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-400">Authentication</span>
              <span className="font-mono text-slate-200">Clerk Multi-Device Persistent Session</span>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
