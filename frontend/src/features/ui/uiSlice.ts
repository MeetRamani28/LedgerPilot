import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface UIState {
  sidebarOpen: boolean
  pdfZoom: number
  selectedLineNumber: number | null
  activeTab: 'invoices' | 'upload' | 'audit' | 'settings'
  isRejectModalOpen: boolean
}

const initialState: UIState = {
  sidebarOpen: true,
  pdfZoom: 1.0,
  selectedLineNumber: null,
  activeTab: 'invoices',
  isRejectModalOpen: false,
}

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload
    },
    zoomIn: (state) => {
      state.pdfZoom = Math.min(2.5, Math.round((state.pdfZoom + 0.15) * 100) / 100)
    },
    zoomOut: (state) => {
      state.pdfZoom = Math.max(0.5, Math.round((state.pdfZoom - 0.15) * 100) / 100)
    },
    resetZoom: (state) => {
      state.pdfZoom = 1.0
    },
    setPdfZoom: (state, action: PayloadAction<number>) => {
      state.pdfZoom = Math.max(0.5, Math.min(2.5, action.payload))
    },
    setSelectedLineNumber: (state, action: PayloadAction<number | null>) => {
      state.selectedLineNumber = action.payload
    },
    setActiveTab: (state, action: PayloadAction<UIState['activeTab']>) => {
      state.activeTab = action.payload
    },
    setRejectModalOpen: (state, action: PayloadAction<boolean>) => {
      state.isRejectModalOpen = action.payload
    },
  },
})

export const {
  toggleSidebar,
  setSidebarOpen,
  zoomIn,
  zoomOut,
  resetZoom,
  setPdfZoom,
  setSelectedLineNumber,
  setActiveTab,
  setRejectModalOpen,
} = uiSlice.actions

export default uiSlice.reducer
