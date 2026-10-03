import React from 'react'
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useAppDispatch, useAppSelector } from '../../app/store'
import { zoomIn, zoomOut, resetZoom } from '../../features/ui/uiSlice'

interface ViewerControlsProps {
  currentPage: number
  numPages: number
  onPrevPage: () => void
  onNextPage: () => void
}

export const ViewerControls: React.FC<ViewerControlsProps> = ({
  currentPage,
  numPages,
  onPrevPage,
  onNextPage,
}) => {
  const dispatch = useAppDispatch()
  const pdfZoom = useAppSelector((state) => state.ui.pdfZoom)

  return (
    <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/90 backdrop-blur text-xs select-none">
      <div className="flex items-center space-x-1.5">
        <button
          onClick={onPrevPage}
          disabled={currentPage <= 1}
          className="rounded p-1 text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent transition-colors cursor-pointer"
          title="Previous Page"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="font-mono text-slate-300 px-1">
          Page {currentPage} of {numPages || 1}
        </span>
        <button
          onClick={onNextPage}
          disabled={currentPage >= numPages}
          className="rounded p-1 text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent transition-colors cursor-pointer"
          title="Next Page"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1 bg-slate-950/60 border border-slate-800 rounded-lg p-0.5">
          <button
            onClick={() => dispatch(zoomOut())}
            disabled={pdfZoom <= 0.5}
            className="rounded p-1 text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 transition-colors cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="font-mono text-slate-300 w-12 text-center text-[11px]">
            {Math.round(pdfZoom * 100)}%
          </span>
          <button
            onClick={() => dispatch(zoomIn())}
            disabled={pdfZoom >= 2.5}
            className="rounded p-1 text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 transition-colors cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
        </div>

        <button
          onClick={() => dispatch(resetZoom())}
          className="rounded p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          title="Reset Zoom to 100%"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
