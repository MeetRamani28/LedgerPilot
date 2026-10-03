import React, { useEffect } from 'react'
import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
  useAuth,
} from '@clerk/clerk-react'
import { setAuthTokenGetter } from '../../lib/api-client'
import { ShieldCheck, Activity, Menu } from 'lucide-react'
import { useAppDispatch, useAppSelector } from '../../app/store'
import { toggleSidebar } from '../../features/ui/uiSlice'

export const Navbar: React.FC = () => {
  const dispatch = useAppDispatch()
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen)
  const { getToken, isSignedIn } = useAuth()

  useEffect(() => {
    if (isSignedIn && getToken) {
      setAuthTokenGetter(() => getToken())
    }
  }, [isSignedIn, getToken])

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors cursor-pointer"
            title={sidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center space-x-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 font-bold text-white shadow-lg shadow-indigo-500/25">
              LP
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold tracking-tight text-white text-base">LedgerPilot</span>
                <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-medium text-indigo-400 border border-indigo-500/20">
                  AP Auto-Pipeline
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">AI-powered 3-way invoice reconciliation</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400 font-medium">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Activity className="h-3.5 w-3.5 mr-1" />
            <span>Groq LPU Vision Ready</span>
          </div>

          <div className="flex items-center space-x-3 pl-2 border-l border-slate-800">
            <SignedIn>
              <UserButton
                appearance={{
                  elements: {
                    userButtonAvatarBox: 'h-8 w-8 ring-2 ring-indigo-500/30',
                  },
                }}
              />
            </SignedIn>
            <SignedOut>
              <SignInButton mode="modal">
                <button className="flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 transition-colors shadow-sm cursor-pointer">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Sign In</span>
                </button>
              </SignInButton>
            </SignedOut>
          </div>
        </div>
      </div>
    </header>
  )
}
