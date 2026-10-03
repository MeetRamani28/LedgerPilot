import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { apiClient } from '../lib/api-client'
import { useAppDispatch } from '../app/store'
import { setSelectedInvoiceId } from '../features/ui/uiSlice'
import { PdfViewer } from '../components/viewer/PdfViewer'

interface InvoiceDetailPageProps {
  invoiceId: string
}

export const InvoiceDetailPage: React.FC<InvoiceDetailPageProps> = ({ invoiceId }) => {
  const dispatch = useAppDispatch()

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: async () => {
      return await apiClient.get<any>(`/api/v1/invoices/${invoiceId}`)
    },
    refetchInterval: (query) => {
      const status = query.state.data?.invoice?.status
      // Auto-poll if pipeline is currently in progress
      if (['UPLOADED', 'EXTRACTING', 'MATCHING', 'ANOMALY_CHECK'].includes(status)) {
        return 2000
      }
      return false
    },
  })

  const invoice = data?.invoice
  const vendor = data?.vendor
  const lineItems = data?.line_items || []
  const anomalies = data?.anomalies || []

  const pdfUrl = invoice?.storage_key
    ? `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/invoices/file/${invoice.storage_key}`
    : ''

  const handleApprove = async () => {
    try {
      await apiClient.post(`/api/v1/invoices/${invoiceId}/approve`)
      toast.success('Invoice approved successfully!')
      refetch()
    } catch (err: any) {
      toast.error(err.message || 'Failed to approve invoice.')
    }
  }

  const handleReject = async () => {
    try {
      await apiClient.post(`/api/v1/invoices/${invoiceId}/reject`, {
        reason: 'Flagged during accounts-payable clerk review',
      })
      toast.warning('Invoice marked as rejected.')
      refetch()
    } catch (err: any) {
      toast.error(err.message || 'Failed to reject invoice.')
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-24 text-slate-400 space-y-3">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm">Loading invoice workspace...</p>
      </div>
    )
  }

  if (!invoice) {
    return (
      <div className="p-8 text-center text-slate-400">
        <AlertTriangle className="h-10 w-10 text-amber-400 mx-auto mb-2" />
        <h3 className="text-base font-medium text-white">Invoice Not Found</h3>
        <button
          onClick={() => dispatch(setSelectedInvoiceId(null))}
          className="mt-4 inline-flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Invoices</span>
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Workspace Header & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => dispatch(setSelectedInvoiceId(null))}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors cursor-pointer"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>All Invoices</span>
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white font-mono">{invoice.invoice_number}</h1>
              <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-400 border border-indigo-500/20">
                {invoice.status}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Vendor: {vendor?.name || 'Pending Extraction'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-white transition-colors cursor-pointer"
            title="Refresh Record"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleReject}
            disabled={invoice.status === 'REJECTED'}
            className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3.5 py-1.5 text-xs font-medium text-rose-400 hover:bg-rose-500/20 transition-colors cursor-pointer disabled:opacity-40"
          >
            Reject
          </button>
          <button
            onClick={handleApprove}
            disabled={invoice.status === 'APPROVED'}
            className="flex items-center space-x-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-emerald-500 transition-colors shadow-sm cursor-pointer disabled:opacity-40"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Approve & Signoff</span>
          </button>
        </div>
      </div>

      {/* Split-Screen Workspace (50% PDF Viewer / 50% Review Panel) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-180px)] min-h-[600px]">
        {/* Left: Document PDF Viewer */}
        <div className="h-full">
          {pdfUrl ? (
            <PdfViewer url={pdfUrl} />
          ) : (
            <div className="h-full rounded-2xl border border-slate-800 bg-slate-900/40 flex items-center justify-center text-slate-500 text-xs">
              No PDF file associated with this record.
            </div>
          )}
        </div>

        {/* Right: Data Review & Reconciliation Panel */}
        <div className="h-full overflow-y-auto space-y-4 pr-1">
          {/* Status & Confidence Banner */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Match Confidence Score</span>
              <span className="font-mono text-sm font-bold text-white">
                {invoice.confidence_score !== null && invoice.confidence_score !== undefined
                  ? `${Math.round(invoice.confidence_score * 100)}%`
                  : 'Computing...'}
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  (invoice.confidence_score || 0) >= 0.9
                    ? 'bg-emerald-500'
                    : (invoice.confidence_score || 0) >= 0.7
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
                style={{ width: `${Math.round((invoice.confidence_score || 0) * 100)}%` }}
              />
            </div>
          </div>

          {/* Anomaly Alerts if present */}
          {anomalies.length > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-semibold">
                <AlertTriangle className="h-4 w-4" />
                <span>Reconciliation Anomaly Flags</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-xs text-amber-300/90">
                {anomalies.map((flag: string, idx: number) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Financial Overview Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Invoice Summary
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-500">Subtotal:</span>
                <p className="font-mono font-semibold text-white mt-0.5">
                  ${invoice.subtotal?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-500">Tax Amount:</span>
                <p className="font-mono font-semibold text-white mt-0.5">
                  ${invoice.tax_amount?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="col-span-2 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-between">
                <span className="text-indigo-300 font-medium">Grand Total:</span>
                <span className="font-mono text-base font-bold text-white">
                  ${invoice.total_amount?.toFixed(2) || '0.00'} {invoice.currency}
                </span>
              </div>
            </div>
          </div>

          {/* Extracted Line Items Preview */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Extracted Line Items ({lineItems.length})
              </h3>
              <span className="text-[11px] text-slate-500">PO Matching Active</span>
            </div>

            {lineItems.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                {invoice.status === 'EXTRACTING' ? (
                  <div className="flex items-center justify-center space-x-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-indigo-400" />
                    <span>Extracting line items via Groq LPU Vision...</span>
                  </div>
                ) : (
                  <span>No line items recorded yet.</span>
                )}
              </div>
            ) : (
              <div className="divide-y divide-slate-800 border border-slate-800 rounded-lg overflow-hidden text-xs">
                {lineItems.map((item: any) => (
                  <div key={item.id} className="p-3 bg-slate-950/40 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-200">{item.description}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Qty: {item.quantity} × ${item.unit_price?.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono font-medium text-white">${item.total_amount?.toFixed(2)}</p>
                      <span
                        className={`inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          item.match_status === 'MATCH'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-amber-500/10 text-amber-400'
                        }`}
                      >
                        {item.match_status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
