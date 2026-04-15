import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, BookOpen, Star, Shield, UserCircle,
  ChevronRight, Zap, Award, X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'
import { useUIStore } from '@/stores/uiStore'
import { Avatar } from '@/components/ui/Avatar'

interface NavItem {
  label: string
  to: string
  icon: React.ReactNode
  roles?: string[]
  bottom?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
  { label: 'Classrooms', to: '/classrooms', icon: <BookOpen className="w-4 h-4" /> },
  { label: 'My Grades', to: '/grades', icon: <Award className="w-4 h-4" />, roles: ['student'] },
  { label: 'Grading', to: '/grading', icon: <Star className="w-4 h-4" />, roles: ['teacher', 'admin'] },
  { label: 'Admin', to: '/admin', icon: <Shield className="w-4 h-4" />, roles: ['admin'] },
  { label: 'Profile', to: '/profile', icon: <UserCircle className="w-4 h-4" />, bottom: true },
]

export function Sidebar() {
  const { user } = useAuthStore()
  const { mobileSidebarOpen, setMobileSidebarOpen } = useUIStore()

  const main = navItems.filter(
    item => !item.bottom && (!item.roles || (user && item.roles.includes(user.role)))
  )
  const bottom = navItems.filter(
    item => item.bottom && (!item.roles || (user && item.roles.includes(user.role)))
  )

  const closeMobile = () => setMobileSidebarOpen(false)

  return (
    <>
      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={closeMobile}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        'fixed left-0 top-0 h-screen w-64 bg-bg-surface/95 backdrop-blur-2xl border-r border-white/10 flex flex-col z-50 transition-transform duration-300 shadow-2xl',
        // On large screens always visible; on mobile show/hide via transform
        'lg:translate-x-0',
        mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
      {/* Logo */}
        <div className="px-5 py-5 flex items-center gap-2.5 border-b border-white/10">
          <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center shadow-glow-sm">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="font-bold text-zinc-100 text-sm tracking-tight">ClassPulse</span>
            {user && <p className="text-[10px] text-zinc-600 capitalize">{user.role}</p>}
          </div>
          {/* Close button — mobile only */}
          <button
            onClick={closeMobile}
            className="lg:hidden p-1 rounded-lg hover:bg-white/6 text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Main nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {main.map(item => (
            <SidebarNavItem key={item.to} item={item} onNavigate={closeMobile} />
          ))}
        </nav>

        {/* Bottom section */}
        <div className="px-3 pb-3 border-t border-white/10 pt-3 space-y-1">
          {bottom.map(item => (
            <SidebarNavItem key={item.to} item={item} onNavigate={closeMobile} />
          ))}

          {user && (
            <NavLink
              to="/profile"
              onClick={closeMobile}
                className="flex items-center gap-2.5 px-3 py-2.5 mt-2 rounded-2xl hover:bg-white/6 transition-colors group cursor-pointer border border-transparent hover:border-white/10"
            >
              <Avatar name={user.full_name} size="sm" src={user.avatar_url} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-zinc-300 truncate">{user.full_name}</p>
                <p className="text-[10px] text-zinc-600">{user.email}</p>
              </div>
            </NavLink>
          )}
        </div>
      </aside>
    </>
  )
}

function SidebarNavItem({ item, onNavigate }: { item: NavItem; onNavigate: () => void }) {
  return (
    <NavLink
      to={item.to}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150 group',
          isActive
            ? 'bg-gradient-to-r from-accent/20 to-blue-500/10 text-zinc-100 border border-accent/30 shadow-inner'
            : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5 border border-transparent'
        )
      }
    >
      {({ isActive }) => (
        <>
          <span className={cn('flex-shrink-0 transition-colors', isActive ? 'text-violet-300' : 'text-zinc-500 group-hover:text-zinc-300')}>
            {item.icon}
          </span>
          <span className="flex-1">{item.label}</span>
          {isActive && <ChevronRight className="w-3 h-3 opacity-50" />}
        </>
      )}
    </NavLink>
  )
}
