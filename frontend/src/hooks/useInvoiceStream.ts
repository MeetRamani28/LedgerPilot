import { useEffect, useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { subscribeToInvoiceEvents, type SSEEventData } from '../lib/sse-client'

export function useInvoiceStream(invoiceId: string | null, initialStatus?: string) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<string>(initialStatus || 'UPLOADED')
  const [progress, setProgress] = useState<number>(initialStatus === 'READY_FOR_REVIEW' ? 100 : 10)
  const [latestMessage, setLatestMessage] = useState<string>('')
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const lastEventIdRef = useRef<string | undefined>(undefined)

  useEffect(() => {
    if (!invoiceId) return

    // Do not stream if already in final state
    if (initialStatus === 'APPROVED' || initialStatus === 'REJECTED') {
      setStatus(initialStatus)
      setProgress(100)
      return
    }

    setIsConnected(true)

    const unsubscribe = subscribeToInvoiceEvents({
      invoiceId,
      lastEventId: lastEventIdRef.current,
      onEvent: (event: SSEEventData) => {
        lastEventIdRef.current = event.event_id
        setStatus(event.status)
        setProgress(event.progress)
        setLatestMessage(event.message)

        // Reactive query invalidation on state changes
        queryClient.invalidateQueries({ queryKey: ['invoice', invoiceId] })
        queryClient.invalidateQueries({ queryKey: ['invoices'] })

        if (event.status === 'READY_FOR_REVIEW') {
          toast.success('3-Way Match & Anomaly Check complete! Ready for signoff.')
          setIsConnected(false)
        } else if (event.type === 'ERROR' || event.status === 'FAILED') {
          toast.error(event.message || 'Pipeline encountered an error.')
          setIsConnected(false)
        }
      },
      onError: () => {
        // Will auto-reconnect via fetch-event-source
      },
      onClose: () => {
        setIsConnected(false)
      },
    })

    return () => {
      unsubscribe()
      setIsConnected(false)
    }
  }, [invoiceId, initialStatus, queryClient])

  return {
    status,
    progress,
    latestMessage,
    isConnected,
  }
}
