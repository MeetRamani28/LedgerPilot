import React from 'react'
import { CheckCircle2, XCircle, RefreshCw, ArrowLeft, ShieldAlert } from 'lucide-react'
import { useAppDispatch } from '../../app/store'
import { setSelectedInvoiceId, setRejectModalOpen } from '../../features/ui/uiSlice'

interface ApprovalActionBarProps {
  invoiceNumber: string
  status: string
  onApprove: () => void
  isApproving?: boolean
  isRejecting?: boolean
  onRefresh: () => void
  isRefreshing?: boolean
}

export const ApprovalActionBar: React.FC<ApprovalActionBarProps> = ({
  invoiceNumber,
  status,
  onApprove,
  isApproving = false,
  onRefresh,
  isRefreshing = false,
}) => {
  const dispatch = useAppDispatch()
  const isFinalized = status === 'APPROVED' || status === 'REJECTED'

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
      <div className="flex items-center space-x-3">
        <button
          onClick={() => dispatch(setSelectedInvoiceId(null))}
          className="flex items-center space-x-1.5 rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>All Invoices</span>
        </button>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold text-white font-mono">{invoiceNumber}</h1>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium border ${
                status === 'APPROVED'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : status === 'REJECTED'
                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
              }`}
            >
              {status.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2.5">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 rounded-xl border border-slate-800 bg-slate-900 text-slate-400 hover:text-white transition-colors cursor-pointer"
          title="Refresh Data"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>

        {!isFinalized && (
          <>
            <button
              onClick={() => dispatch(setRejectModalOpen(true))}
              className="flex items-center space-x-1.5 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3.5 py-2 text-xs font-medium text-rose-400 hover:bg-rose-500/20 transition-colors cursor-pointer"
            >
              <XCircle className="h-3.5 w-3.5" />
              <span>Reject with Reason</span>
            </button>

            <button
              onClick={onApprove}
              disabled={isApproving}
              className="flex items-center space-x-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-medium text-white hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-600/20 cursor-pointer disabled:opacity-50"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{isApproving ? 'Approving...' : 'Approve & Signoff'}</span>
            </button>
          </>
        )}

        {isFinalized && (
          <div className="flex items-center space-x-1.5 text-xs text-slate-400">
            <ShieldAlert className="h-4 w-4 text-slate-500" />
            <span>Workflow Locked ({status})</span>
          </div>
        )}
      </div>
    </div>
  )
}
