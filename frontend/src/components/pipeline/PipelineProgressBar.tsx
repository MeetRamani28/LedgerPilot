import React from 'react'
import {
  UploadCloud,
  FileSearch,
  Layers,
  ShieldAlert,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react'

interface PipelineProgressBarProps {
  status: string
  progress: number
  message?: string
  isConnected?: boolean
}

const STAGES = [
  { id: 'UPLOADED', label: 'Uploaded', icon: UploadCloud, minProgress: 10 },
  { id: 'EXTRACTING', label: 'Vision Extraction', icon: FileSearch, minProgress: 20 },
  { id: 'MATCHING', label: '3-Way Match', icon: Layers, minProgress: 50 },
  { id: 'ANOMALY_CHECK', label: 'Anomaly Check', icon: ShieldAlert, minProgress: 80 },
  { id: 'READY_FOR_REVIEW', label: 'Ready for Review', icon: CheckCircle2, minProgress: 100 },
]

export const PipelineProgressBar: React.FC<PipelineProgressBarProps> = ({
  status,
  progress,
  message,
  isConnected = false,
}) => {
  const isFinalized = status === 'APPROVED' || status === 'REJECTED' || status === 'READY_FOR_REVIEW'
  const isFailed = status === 'FAILED'

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm space-y-4">
      {/* Header telemetry */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Autonomous AP Pipeline
          </span>
          {isConnected && (
            <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
              <span>Live SSE Stream</span>
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400">Progress:</span>
          <span className="font-mono text-xs font-bold text-indigo-400">{progress}%</span>
        </div>
      </div>

      {/* Stepper Dots */}
      <div className="relative">
        {/* Continuous Bar Behind */}
        <div className="absolute top-4 left-6 right-6 h-0.5 bg-slate-800 -z-0" />
        <div
          className="absolute top-4 left-6 h-0.5 bg-gradient-to-r from-indigo-500 to-emerald-500 transition-all duration-500 -z-0"
          style={{ width: `${Math.max(0, Math.min(100, (progress - 10) * 1.15))}%` }}
        />

        <div className="grid grid-cols-5 gap-2 relative z-10">
          {STAGES.map((stage) => {
            const Icon = stage.icon
            const isCompleted = progress >= stage.minProgress
            const isCurrent =
              status === stage.id ||
              (progress >= stage.minProgress - 15 && progress < stage.minProgress + 15)

            return (
              <div key={stage.id} className="flex flex-col items-center text-center space-y-2">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full border transition-all ${
                    isCompleted
                      ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400 shadow-sm shadow-emerald-500/20'
                      : isCurrent
                      ? 'border-indigo-400 bg-indigo-500/20 text-indigo-300 ring-4 ring-indigo-500/10 animate-pulse'
                      : 'border-slate-800 bg-slate-950 text-slate-600'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <span
                  className={`text-[10px] font-medium leading-tight ${
                    isCompleted
                      ? 'text-slate-200'
                      : isCurrent
                      ? 'text-indigo-400 font-semibold'
                      : 'text-slate-600'
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Live Telemetry Message */}
      {message && (
        <div className="flex items-center space-x-2 pt-2 border-t border-slate-800/80 text-xs text-slate-300">
          {!isFinalized && !isFailed && (
            <RefreshCw className="h-3.5 w-3.5 animate-spin text-indigo-400 shrink-0" />
          )}
          {isFinalized && (
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          )}
          <span className="font-mono text-[11px] truncate">{message}</span>
        </div>
      )}
    </div>
  )
}
