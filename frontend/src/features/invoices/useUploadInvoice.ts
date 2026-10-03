import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiClient } from '../../lib/api-client'
import { useAppDispatch } from '../../app/store'
import { setSelectedInvoiceId, setActiveTab } from '../ui/uiSlice'

export interface UploadResponse {
  message: string
  invoice_id: string
  status: string
  is_duplicate?: boolean
}

export function useUploadInvoice() {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()

  return useMutation({
    mutationFn: async (file: File): Promise<UploadResponse> => {
      // Validate file type
      if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
        throw new Error('Please select a valid PDF invoice document.')
      }

      // Validate size (15MB limit)
      const MAX_SIZE = 15 * 1024 * 1024
      if (file.size > MAX_SIZE) {
        throw new Error('File exceeds maximum allowed size of 15MB.')
      }

      const formData = new FormData()
      formData.append('file', file)

      return await apiClient.post<UploadResponse>('/api/v1/invoices/upload', formData)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      if (data.is_duplicate) {
        toast.warning('Duplicate invoice detected. Opening existing record.')
      } else {
        toast.success('Invoice uploaded! Autonomous pipeline initiated.')
      }
      dispatch(setSelectedInvoiceId(data.invoice_id))
      dispatch(setActiveTab('invoices'))
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to upload invoice.')
    },
  })
}
