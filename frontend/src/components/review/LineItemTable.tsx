import React, { useState } from 'react'
import { Edit2, Check, X, Layers, AlertCircle } from 'lucide-react'
import { MatchStatusBadge } from './MatchStatusBadge'
import { useUpdateLineItem } from '../../features/invoices/useInvoiceActions'
import { useAppDispatch, useAppSelector } from '../../app/store'
import { setSelectedLineNumber } from '../../features/ui/uiSlice'

interface LineItem {
  id: string
  line_number: number
  description: string
  quantity: number
  unit_price: number
  total_amount: number
  match_status: string
  price_variance?: number
  quantity_variance?: number
  mismatch_reason?: string
}

interface LineItemTableProps {
  invoiceId: string
  lineItems: LineItem[]
}

export const LineItemTable: React.FC<LineItemTableProps> = ({ invoiceId, lineItems }) => {
  const dispatch = useAppDispatch()
  const selectedLineNumber = useAppSelector((state) => state.ui.selectedLineNumber)
  const updateLineItem = useUpdateLineItem(invoiceId)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<{
    description: string
    quantity: number
    unit_price: number
  }>({
    description: '',
    quantity: 1,
    unit_price: 0,
  })

  const handleStartEdit = (item: LineItem) => {
    setEditingId(item.id)
    setEditForm({
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unit_price,
    })
  }

  const handleCancelEdit = () => {
    setEditingId(null)
  }

  const handleSaveEdit = (lineItemId: string) => {
    updateLineItem.mutate(
      {
        lineItemId,
        description: editForm.description,
        quantity: Number(editForm.quantity),
        unit_price: Number(editForm.unit_price),
      },
      {
        onSuccess: () => {
          setEditingId(null)
        },
      },
    )
  }

  if (lineItems.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-500 text-xs">
        <Layers className="h-6 w-6 text-slate-600 mx-auto mb-2" />
        <span>No line items extracted for this invoice yet.</span>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Reconciled Line Items ({lineItems.length})
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Select or edit any row to correct quantities, pricing, and re-evaluate 3-way match.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3 font-medium w-12 text-center">#</th>
              <th className="py-2.5 px-3 font-medium">Description</th>
              <th className="py-2.5 px-3 font-medium text-right w-24">Qty</th>
              <th className="py-2.5 px-3 font-medium text-right w-28">Unit Price</th>
              <th className="py-2.5 px-3 font-medium text-right w-28">Total</th>
              <th className="py-2.5 px-3 font-medium text-center w-36">Match Status</th>
              <th className="py-2.5 px-3 font-medium text-right w-20">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {lineItems.map((item) => {
              const isEditing = editingId === item.id
              const isSelected = selectedLineNumber === item.line_number

              return (
                <tr
                  key={item.id}
                  onClick={() => dispatch(setSelectedLineNumber(item.line_number))}
                  className={`transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-600/15 border-l-2 border-indigo-500'
                      : 'hover:bg-slate-800/40'
                  }`}
                >
                  <td className="py-3 px-3 text-center font-mono text-slate-400">
                    {item.line_number}
                  </td>

                  <td className="py-3 px-3">
                    {isEditing ? (
                      <input
                        type="text"
                        value={editForm.description}
                        onChange={(e) =>
                          setEditForm({ ...editForm, description: e.target.value })
                        }
                        className="w-full rounded bg-slate-950 border border-slate-700 px-2 py-1 text-white text-xs focus:outline-none focus:border-indigo-500"
                      />
                    ) : (
                      <div>
                        <p className="font-medium text-slate-200">{item.description}</p>
                        {item.mismatch_reason && (
                          <p className="text-[10px] text-amber-400 mt-0.5 flex items-center">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            {item.mismatch_reason.replace('_', ' ')}
                          </p>
                        )}
                      </div>
                    )}
                  </td>

                  <td className="py-3 px-3 text-right">
                    {isEditing ? (
                      <input
                        type="number"
                        step="any"
                        value={editForm.quantity}
                        onChange={(e) =>
                          setEditForm({ ...editForm, quantity: parseFloat(e.target.value) || 0 })
                        }
                        className="w-20 rounded bg-slate-950 border border-slate-700 px-2 py-1 text-white text-xs text-right focus:outline-none focus:border-indigo-500"
                      />
                    ) : (
                      <span className="font-mono text-slate-300">{item.quantity}</span>
                    )}
                  </td>

                  <td className="py-3 px-3 text-right">
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.01"
                        value={editForm.unit_price}
                        onChange={(e) =>
                          setEditForm({ ...editForm, unit_price: parseFloat(e.target.value) || 0 })
                        }
                        className="w-24 rounded bg-slate-950 border border-slate-700 px-2 py-1 text-white text-xs text-right focus:outline-none focus:border-indigo-500"
                      />
                    ) : (
                      <span className="font-mono text-slate-300">
                        ${item.unit_price?.toFixed(2)}
                      </span>
                    )}
                  </td>

                  <td className="py-3 px-3 text-right font-mono font-medium text-white">
                    {isEditing ? (
                      <span>
                        ${(editForm.quantity * editForm.unit_price).toFixed(2)}
                      </span>
                    ) : (
                      <span>${item.total_amount?.toFixed(2)}</span>
                    )}
                  </td>

                  <td className="py-3 px-3 text-center">
                    <MatchStatusBadge
                      status={item.match_status}
                      variancePct={item.price_variance}
                    />
                  </td>

                  <td className="py-3 px-3 text-right">
                    {isEditing ? (
                      <div className="flex items-center justify-end space-x-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSaveEdit(item.id)
                          }}
                          disabled={updateLineItem.isPending}
                          className="rounded p-1 text-emerald-400 hover:bg-emerald-500/10 cursor-pointer"
                          title="Save corrections"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleCancelEdit()
                          }}
                          className="rounded p-1 text-slate-400 hover:bg-slate-800 cursor-pointer"
                          title="Cancel"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStartEdit(item)
                        }}
                        className="rounded p-1 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition-colors cursor-pointer"
                        title="Edit Line Item"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
