import React from 'react'
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react'

interface MatchStatusBadgeProps {
  status: 'MATCH' | 'PRICE_VARIANCE' | 'QUANTITY_DISCREPANCY' | 'UNMATCHED' | string
  variancePct?: number
  className?: string
}

export const MatchStatusBadge: React.FC<MatchStatusBadgeProps> = ({
  status,
  variancePct,
  className = '',
}) => {
  switch (status) {
    case 'MATCH':
      return (
        <span
          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 ${className}`}
        >
          <CheckCircle2 className="h-3 w-3" />
          <span>3-Way Match</span>
        </span>
      )
    case 'PRICE_VARIANCE':
      return (
        <span
          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 ${className}`}
        >
          <AlertTriangle className="h-3 w-3" />
          <span>
            Price Drift {variancePct ? `(${Math.round(variancePct * 100)}%)` : ''}
          </span>
        </span>
      )
    case 'QUANTITY_DISCREPANCY':
      return (
        <span
          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20 ${className}`}
        >
          <AlertTriangle className="h-3 w-3" />
          <span>Qty Discrepancy</span>
        </span>
      )
    case 'UNMATCHED':
      return (
        <span
          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 ${className}`}
        >
          <AlertCircle className="h-3 w-3" />
          <span>Unmatched</span>
        </span>
      )
    default:
      return (
        <span
          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-300 ${className}`}
        >
          <HelpCircle className="h-3 w-3" />
          <span>{status}</span>
        </span>
      )
  }
}
