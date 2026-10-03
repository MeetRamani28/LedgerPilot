import React, { useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { FileWarning, Loader2 } from 'lucide-react'
import { useAppSelector } from '../../app/store'
import { ViewerControls } from './ViewerControls'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface PdfViewerProps {
  url: string
}

export const PdfViewer: React.FC<PdfViewerProps> = ({ url }) => {
  const [numPages, setNumPages] = useState<number>(1)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [loadError, setLoadError] = useState<string | null>(null)
  const pdfZoom = useAppSelector((state) => state.ui.pdfZoom)

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setCurrentPage(1)
    setLoadError(null)
  }

  const onDocumentLoadError = (error: Error) => {
    console.error('Failed to load PDF via react-pdf:', error)
    setLoadError(error.message)
  }

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-lg">
      <ViewerControls
        currentPage={currentPage}
        numPages={numPages}
        onPrevPage={() => setCurrentPage((p) => Math.max(1, p - 1))}
        onNextPage={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
      />

      <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-slate-950/80">
        {loadError ? (
          <div className="text-center p-6 max-w-sm">
            <FileWarning className="h-10 w-10 text-amber-400 mx-auto mb-2" />
            <h4 className="text-sm font-medium text-slate-200">Unable to render PDF canvas</h4>
            <p className="text-xs text-slate-400 mt-1 mb-4">{loadError}</p>
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center text-xs font-medium text-indigo-400 hover:text-indigo-300 underline"
            >
              Open PDF directly in new tab
            </a>
          </div>
        ) : (
          <div
            className="transition-transform duration-150 origin-top flex justify-center shadow-2xl rounded-lg overflow-hidden border border-slate-800"
            style={{ transform: `scale(${pdfZoom})` }}
          >
            <Document
              file={url}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex flex-col items-center justify-center p-16 text-slate-400 space-y-2">
                  <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
                  <span className="text-xs">Loading PDF document...</span>
                </div>
              }
            >
              <Page
                pageNumber={currentPage}
                renderTextLayer={true}
                renderAnnotationLayer={false}
                className="bg-white"
              />
            </Document>
          </div>
        )}
      </div>
    </div>
  )
}
