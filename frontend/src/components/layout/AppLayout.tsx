import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { useWebSocket } from '@/hooks/useWebSocket'
import { CommandPalette } from '@/components/CommandPalette'

export function AppLayout() {
  useWebSocket() // establish WS connection for authenticated user

  return (
    <div className="min-h-screen bg-bg-base app-shell-bg">
      <CommandPalette />
      <Sidebar />
      <Topbar />
      <main className="ml-64 pt-16 min-h-screen max-lg:ml-0">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
