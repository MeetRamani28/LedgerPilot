import React from 'react'
import { DollarSign, AlertCircle } from 'lucide-react'

interface ToleranceVarianceCardProps {
  subtotal: number
  taxAmount: number
  totalAmount: number
  currency?: string
  anomalies?: string[]
}

export const ToleranceVarianceCard: React.FC<ToleranceVarianceCardProps> = ({
  subtotal,
  taxAmount,
  totalAmount,
  currency = 'USD',
  anomalies = [],
}) => {
  const taxRate = subtotal > 0 ? (taxAmount / subtotal) * 100 : 0

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
          <DollarSign className="h-3.5 w-3.5 text-indigo-400" />
          <span>Financial Verification & Totals</span>
        </h3>
        <span className="text-[11px] font-mono text-slate-400">
          Tax Rate: {taxRate.toFixed(1)}%
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/60">
          <span className="text-slate-500">Subtotal</span>
          <p className="font-mono text-sm font-semibold text-white mt-1">
            ${subtotal?.toFixed(2) || '0.00'}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/60">
          <span className="text-slate-500">Tax Amount</span>
          <p className="font-mono text-sm font-semibold text-white mt-1">
            ${taxAmount?.toFixed(2) || '0.00'}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
          <span className="text-indigo-300 font-medium">Grand Total</span>
          <p className="font-mono text-sm font-bold text-white mt-1">
            ${totalAmount?.toFixed(2) || '0.00'} {currency}
          </p>
        </div>
      </div>

      {anomalies.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 space-y-1.5">
          <div className="flex items-center space-x-1.5 text-amber-400 text-xs font-semibold">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>Reconciliation Warnings ({anomalies.length})</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-300/90">
            {anomalies.map((anomaly, idx) => (
              <li key={idx}>{anomaly}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
