import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, AlertTriangle, RefreshCw } from 'lucide-react'
import { apiClient } from '../lib/api-client'
import { useAppDispatch, useAppSelector } from '../app/store'
import { setSelectedInvoiceId, setRejectModalOpen } from '../features/ui/uiSlice'
import { PdfViewer } from '../components/viewer/PdfViewer'
import { InvoiceHeaderCard } from '../components/review/InvoiceHeaderCard'
import { ToleranceVarianceCard } from '../components/review/ToleranceVarianceCard'
import { LineItemTable } from '../components/review/LineItemTable'
import { ApprovalActionBar } from '../components/review/ApprovalActionBar'
import { RejectReasonModal } from '../components/review/RejectReasonModal'
import { PipelineProgressBar } from '../components/pipeline/PipelineProgressBar'
import { useInvoiceStream } from '../hooks/useInvoiceStream'
import {
  useApproveInvoice,
  useRejectInvoice,
} from '../features/invoices/useInvoiceActions'

interface InvoiceDetailPageProps {
  invoiceId: string
}

export const InvoiceDetailPage: React.FC<InvoiceDetailPageProps> = ({ invoiceId }) => {
  const dispatch = useAppDispatch()
  const isRejectModalOpen = useAppSelector((state) => state.ui.isRejectModalOpen)

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: async () => {
      return await apiClient.get<any>(`/api/v1/invoices/${invoiceId}`)
    },
  })

  const invoice = data?.invoice
  const vendor = data?.vendor
  const lineItems = data?.line_items || []
  const anomalies = data?.anomalies || []

  // Connect real-time Server-Sent Events stream
  const {
    status: liveStatus,
    progress: liveProgress,
    latestMessage,
    isConnected,
  } = useInvoiceStream(invoiceId, invoice?.status)

  const currentStatus = liveStatus || invoice?.status || 'UPLOADED'

  const approveMutation = useApproveInvoice(invoiceId)
  const rejectMutation = useRejectInvoice(invoiceId)

  const pdfUrl = invoice?.storage_key
    ? `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/invoices/file/${invoice.storage_key}`
    : ''

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-24 text-slate-400 space-y-3">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm">Loading invoice reconciliation workspace...</p>
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
      {/* Action Bar */}
      <ApprovalActionBar
        invoiceNumber={invoice.invoice_number || 'PENDING'}
        status={currentStatus}
        onApprove={() => approveMutation.mutate()}
        isApproving={approveMutation.isPending}
        onRefresh={() => refetch()}
        isRefreshing={isFetching}
      />

      {/* Real-time Pipeline Progress Stepper */}
      <PipelineProgressBar
        status={currentStatus}
        progress={liveProgress}
        message={latestMessage}
        isConnected={isConnected}
      />

      {/* Split-Screen Workspace (50% PDF Viewer / 50% Review Panel) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-290px)] min-h-[580px]">
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

        {/* Right: Data Review, Editable Line Items & Variance Badges */}
        <div className="h-full overflow-y-auto space-y-4 pr-1">
          <InvoiceHeaderCard invoice={invoice} vendor={vendor} />

          <ToleranceVarianceCard
            subtotal={invoice.subtotal}
            taxAmount={invoice.tax_amount}
            totalAmount={invoice.total_amount}
            currency={invoice.currency}
            anomalies={anomalies}
          />

          <LineItemTable invoiceId={invoice.id} lineItems={lineItems} />
        </div>
      </div>

      {/* Reject Modal */}
      <RejectReasonModal
        isOpen={isRejectModalOpen}
        onClose={() => dispatch(setRejectModalOpen(false))}
        isSubmitting={rejectMutation.isPending}
        onConfirm={(reason) => {
          rejectMutation.mutate(reason, {
            onSuccess: () => dispatch(setRejectModalOpen(false)),
          })
        }}
      />
    </div>
  )
}
