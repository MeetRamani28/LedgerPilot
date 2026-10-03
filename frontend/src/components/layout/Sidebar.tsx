import React from 'react'
import {
  FileText,
  UploadCloud,
  History,
  Sliders,
  Database,
  Layers,
  type LucideIcon,
} from 'lucide-react'
import { useAppDispatch, useAppSelector } from '../../app/store'
import { setActiveTab, type UIState } from '../../features/ui/uiSlice'

interface NavItem {
  id: UIState['activeTab']
  label: string
  icon: LucideIcon
  badge?: string
}

export const Sidebar: React.FC = () => {
  const dispatch = useAppDispatch()
  const { sidebarOpen, activeTab } = useAppSelector((state) => state.ui)

  const navItems: NavItem[] = [
    {
      id: 'invoices',
      label: 'Invoices & Review',
      icon: FileText,
      badge: 'Active',
    },
    {
      id: 'upload',
      label: 'Upload Pipeline',
      icon: UploadCloud,
    },
    {
      id: 'audit',
      label: 'Audit & Compliance',
      icon: History,
    },
    {
      id: 'settings',
      label: 'Telemetry & Config',
      icon: Sliders,
    },
  ]

  if (!sidebarOpen) {
    return (
      <aside className="w-16 border-r border-slate-800 bg-slate-950/60 flex flex-col items-center py-4 space-y-3 transition-all duration-200">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => dispatch(setActiveTab(item.id))}
              title={item.label}
              className={`p-2.5 rounded-xl transition-all cursor-pointer ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Icon className="h-5 w-5" />
            </button>
          )
        })}
      </aside>
    )
  }

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between transition-all duration-200">
      <div className="space-y-6">
        <div>
          <p className="px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
            AP Workflow
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => dispatch(setActiveTab(item.id))}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] text-indigo-300">
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 text-xs space-y-2">
          <div className="flex items-center space-x-2 text-slate-300 font-medium">
            <Layers className="h-3.5 w-3.5 text-indigo-400" />
            <span>3-Way Engine</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Reconciles Line Items vs Purchase Orders vs Goods Receipts with anomaly detection.
          </p>
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
            <span>Provider</span>
            <span className="font-mono text-slate-400">Groq + Chroma</span>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800/60">
        <div className="flex items-center space-x-2 text-[11px] text-slate-500">
          <Database className="h-3.5 w-3.5 text-emerald-400" />
          <span>Local SQLite / ChromaDB</span>
        </div>
      </div>
    </aside>
  )
}
