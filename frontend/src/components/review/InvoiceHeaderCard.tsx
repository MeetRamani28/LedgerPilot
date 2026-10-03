import React from 'react'
import { Building2, Calendar, FileSpreadsheet, ShieldCheck, Tag } from 'lucide-react'

interface InvoiceHeaderCardProps {
  invoice: any
  vendor: any
}

export const InvoiceHeaderCard: React.FC<InvoiceHeaderCardProps> = ({ invoice, vendor }) => {
  const confidence = invoice.confidence_score !== null && invoice.confidence_score !== undefined
    ? Math.round(invoice.confidence_score * 100)
    : null

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm space-y-4">
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Building2 className="h-4 w-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-white">
            {vendor?.name || 'Unregistered Vendor'}
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          {confidence !== null && (
            <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 border border-slate-700">
              <ShieldCheck
                className={`h-3.5 w-3.5 ${
                  confidence >= 90
                    ? 'text-emerald-400'
                    : confidence >= 70
                    ? 'text-amber-400'
                    : 'text-rose-400'
                }`}
              />
              <span className="text-slate-300">Confidence:</span>
              <span className="font-mono text-white font-bold">{confidence}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Grid Details */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/60">
          <span className="text-slate-500 flex items-center space-x-1">
            <Tag className="h-3 w-3 mr-1" /> Invoice #
          </span>
          <p className="font-mono font-medium text-slate-200 mt-1 truncate">
            {invoice.invoice_number || 'PENDING'}
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/60">
          <span className="text-slate-500 flex items-center space-x-1">
            <Calendar className="h-3 w-3 mr-1" /> Invoice Date
          </span>
          <p className="text-slate-200 mt-1">
            {invoice.invoice_date || new Date(invoice.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/60">
          <span className="text-slate-500 flex items-center space-x-1">
            <FileSpreadsheet className="h-3 w-3 mr-1" /> Purchase Order
          </span>
          <p className="font-mono font-medium text-indigo-300 mt-1 truncate">
            {vendor?.payment_terms || 'Net 30'}
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/60">
          <span className="text-slate-500">Tax ID / VAT</span>
          <p className="font-mono text-slate-300 mt-1 truncate">
            {vendor?.tax_id || 'Not specified'}
          </p>
        </div>
      </div>
    </div>
  )
}
