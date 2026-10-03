import React, { useRef, useState } from 'react'
import { UploadCloud, FileText, AlertCircle, RefreshCw } from 'lucide-react'
import { useUploadInvoice } from '../../features/invoices/useUploadInvoice'

export const FileUploadDropzone: React.FC = () => {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { mutate: uploadFile, isPending, error } = useUploadInvoice()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      uploadFile(file)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      uploadFile(file)
    }
  }

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isPending && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer ${
          isDragOver
            ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]'
            : 'border-slate-700/80 bg-slate-900/40 hover:border-indigo-500/80 hover:bg-slate-900/60'
        } ${isPending ? 'opacity-70 pointer-events-none' : ''}`}
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 mb-4 border border-indigo-500/20">
          {isPending ? (
            <RefreshCw className="h-8 w-8 animate-spin" />
          ) : (
            <UploadCloud className="h-8 w-8" />
          )}
        </div>

        {isPending ? (
          <div>
            <h3 className="text-base font-medium text-white">Uploading & Rasterizing PDF...</h3>
            <p className="text-xs text-slate-400 mt-1">Initiating Groq LPU Vision and 3-Way Match Engine</p>
          </div>
        ) : (
          <div>
            <h3 className="text-base font-semibold text-white">Drag & drop invoice PDF here</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              or <span className="text-indigo-400 underline decoration-indigo-400/50 underline-offset-2">browse files</span> from your computer
            </p>
            <div className="mt-4 flex items-center justify-center space-x-4 text-[11px] text-slate-500">
              <span className="flex items-center">
                <FileText className="h-3.5 w-3.5 mr-1 text-slate-400" /> PDF Only
              </span>
              <span>•</span>
              <span>Up to 15MB</span>
              <span>•</span>
              <span>Multi-page invoices supported</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-center space-x-2 rounded-lg bg-rose-500/10 border border-rose-500/20 px-4 py-2.5 text-xs text-rose-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error.message}</span>
        </div>
      )}
    </div>
  )
}
