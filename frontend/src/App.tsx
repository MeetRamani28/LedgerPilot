export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            LP
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white">LedgerPilot</h1>
            <p className="text-xs text-slate-400">Autonomous AP & 3-Way Invoice Reconciliation</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Engine Online
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-sm">
              <h2 className="text-base font-medium text-white mb-2">Invoice Reconciliation Pipeline</h2>
              <p className="text-sm text-slate-400 mb-6">
                Upload accounts-payable invoices to trigger autonomous extraction, PO matching, and anomaly checks.
              </p>
              
              <div className="border-2 border-dashed border-slate-700/80 hover:border-indigo-500/80 transition-colors rounded-xl p-8 text-center bg-slate-950/40 cursor-pointer">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 mb-3">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-slate-200">Drag & drop invoice PDF here</h3>
                <p className="text-xs text-slate-500 mt-1">Supports multi-page PDF up to 15MB</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-sm">
              <h3 className="text-sm font-medium text-slate-200 mb-3">System Pipeline Telemetry</h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center text-slate-400">
                  <span>Relational DB:</span>
                  <span className="font-mono text-slate-300">SQLite (Local)</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Vector Index:</span>
                  <span className="font-mono text-slate-300">ChromaDB</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Vision Engine:</span>
                  <span className="font-mono text-slate-300">Groq LPU Vision</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Authentication:</span>
                  <span className="font-mono text-slate-300">Clerk Multi-Session</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
