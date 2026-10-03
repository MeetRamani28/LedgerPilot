import { fetchEventSource } from '@microsoft/fetch-event-source'
import { getAuthToken } from './api-client'

export interface SSEEventData {
  event_id: string
  type: string
  invoice_id: string
  status: string
  progress: number
  message: string
  timestamp: string
}

export interface SubscribeSSEOptions {
  invoiceId: string
  onEvent: (event: SSEEventData) => void
  onError?: (error: any) => void
  onClose?: () => void
  lastEventId?: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function subscribeToInvoiceEvents(options: SubscribeSSEOptions): () => void {
  const ctrl = new AbortController()
  const { invoiceId, onEvent, onError, onClose, lastEventId } = options

  const connect = async () => {
    const token = await getAuthToken()
    const headers: Record<string, string> = {
      Accept: 'text/event-stream',
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    } else {
      headers['Authorization'] = 'Bearer test_token_dev_user'
    }

    if (lastEventId) {
      headers['Last-Event-ID'] = lastEventId
    }

    const url = `${API_BASE_URL}/api/v1/invoices/${invoiceId}/events`

    try {
      await fetchEventSource(url, {
        method: 'GET',
        headers,
        signal: ctrl.signal,
        async onopen(response) {
          if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
            return // connection open
          } else {
            console.warn('SSE non-200 or non-event-stream response', response.status)
          }
        },
        onmessage(msg) {
          // Ignore comment heartbeats
          if (!msg.data) return

          try {
            const parsed = JSON.parse(msg.data) as SSEEventData
            onEvent(parsed)
          } catch (e) {
            console.warn('Unable to parse SSE event data', msg.data, e)
          }
        },
        onclose() {
          if (onClose) onClose()
        },
        onerror(err) {
          if (ctrl.signal.aborted) return
          console.warn('SSE stream error, retrying...', err)
          if (onError) onError(err)
        },
      })
    } catch (err: any) {
      if (!ctrl.signal.aborted && onError) {
        onError(err)
      }
    }
  }

  connect()

  // Return unsubscribe/abort function
  return () => {
    ctrl.abort()
  }
}
