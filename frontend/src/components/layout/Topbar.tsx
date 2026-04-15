import { useLocation } from 'react-router-dom'
import { LogOut, Menu, Command } from 'lucide-react'
import { NotificationBell } from '@/components/notifications/NotificationBell'
import { useAuth } from '@/hooks/useAuth'
import { useUIStore } from '@/stores/uiStore'

const routeTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/classrooms': 'Classrooms',
  '/assignments': 'Assignments',
  '/grading': 'Grading',
  '/grades': 'My Grades',
  '/profile': 'Profile',
  '/admin': 'Admin',
}

function getTitle(pathname: string): string {
  // Exact match first
  if (routeTitles[pathname]) return routeTitles[pathname]
  // Prefix match
  for (const [key, val] of Object.entries(routeTitles)) {
    if (pathname.startsWith(key + '/')) return val
  }
  return 'ClassPulse'
}

export function Topbar() {
  const { pathname } = useLocation()
  const { logout } = useAuth()
  const { toggleCommandPalette, toggleMobileSidebar } = useUIStore()

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-bg-base/65 backdrop-blur-xl border-b border-white/10 flex items-center justify-between px-4 sm:px-6 z-20 max-lg:left-0">
      <div className="flex items-center gap-3">
        {/* Hamburger — mobile only */}
        <button
          onClick={toggleMobileSidebar}
          className="lg:hidden p-2 rounded-xl hover:bg-white/6 text-zinc-500 hover:text-zinc-300 transition-colors"
          title="Open menu"
        >
          <Menu className="w-4 h-4" />
        </button>
        <h1 className="text-sm sm:text-base font-semibold text-zinc-100 tracking-tight">{getTitle(pathname)}</h1>
      </div>

      <div className="flex items-center gap-1.5">
        {/* Command palette trigger */}
        <button
          onClick={toggleCommandPalette}
          className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl bg-bg-surface/70 hover:bg-bg-surface text-zinc-400 hover:text-zinc-200 transition-colors border border-white/10 text-xs"
          title="Open command palette (Ctrl+K)"
        >
          <Command className="w-3.5 h-3.5" />
          <span className="text-zinc-500">Search</span>
          <span className="rounded-md border border-white/15 px-1.5 py-0.5 text-[10px] text-zinc-500">⌘K</span>
        </button>
        <button
          onClick={toggleCommandPalette}
          className="sm:hidden p-2 rounded-xl hover:bg-white/6 text-zinc-500 hover:text-zinc-300 transition-colors"
          title="Search"
        >
          <Command className="w-4 h-4" />
        </button>

        <NotificationBell />
        <button
          onClick={() => logout()}
          className="p-2 rounded-xl hover:bg-white/6 text-zinc-500 hover:text-zinc-300 transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
