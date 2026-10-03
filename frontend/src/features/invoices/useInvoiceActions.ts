import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiClient } from '../../lib/api-client'

export function useApproveInvoice(invoiceId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      return await apiClient.post(`/api/v1/invoices/${invoiceId}/approve`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', invoiceId] })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      queryClient.invalidateQueries({ queryKey: ['audit-logs'] })
      toast.success('Invoice approved and recorded in accounts-payable ledger!')
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to approve invoice.')
    },
  })
}

export function useRejectInvoice(invoiceId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (reason: string) => {
      return await apiClient.post(`/api/v1/invoices/${invoiceId}/reject`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', invoiceId] })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      queryClient.invalidateQueries({ queryKey: ['audit-logs'] })
      toast.warning('Invoice rejected and flagged for vendor review.')
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to reject invoice.')
    },
  })
}

export interface LineItemUpdatePayload {
  lineItemId: string
  description?: string
  quantity?: number
  unit_price?: number
}

export function useUpdateLineItem(invoiceId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: LineItemUpdatePayload) => {
      const { lineItemId, ...data } = payload
      return await apiClient.patch(
        `/api/v1/invoices/${invoiceId}/line-items/${lineItemId}`,
        data,
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', invoiceId] })
      toast.success('Line item corrected and totals recalculated.')
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to update line item.')
    },
  })
}
