import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, BookOpen, Users, LayoutDashboard, GraduationCap, X } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { classroomsApi } from '@/api/classrooms'

interface Action {
  id: string
  label: string
  sublabel?: string
  icon: React.ReactNode
  action: () => void
}

function fuzzyMatch(haystack: string, needle: string): boolean {
  if (!needle) return true
  const h = haystack.toLowerCase()
  const n = needle.toLowerCase()
  return h.includes(n)
}

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: classrooms = [] } = useQuery({
    queryKey: ['classrooms'],
    queryFn: () => classroomsApi.list(),
    enabled: commandPaletteOpen,
  })

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const close = useCallback(() => {
    setCommandPaletteOpen(false)
    setQuery('')
    setSelected(0)
  }, [setCommandPaletteOpen])

  useEffect(() => {
    if (commandPaletteOpen) {
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [commandPaletteOpen])

  // Global Cmd+K / Ctrl+K listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(!commandPaletteOpen)
      }
      if (e.key === 'Escape') close()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [commandPaletteOpen, setCommandPaletteOpen, close])

  const staticActions: Action[] = [
    {
      id: 'dashboard',
      label: 'Go to Dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
      action: () => { navigate('/dashboard'); close() },
    },
    {
      id: 'classrooms',
      label: 'My Classrooms',
      icon: <BookOpen className="w-4 h-4" />,
      action: () => { navigate('/classrooms'); close() },
    },
    ...(isTeacher ? [{
      id: 'grading',
      label: 'Grading Queue',
      icon: <GraduationCap className="w-4 h-4" />,
      action: () => { navigate('/grading'); close() },
    }] : []),
    {
      id: 'grades',
      label: 'My Grades',
      icon: <GraduationCap className="w-4 h-4" />,
      action: () => { navigate('/grades'); close() },
    },
    {
      id: 'profile',
      label: 'Profile Settings',
      icon: <Users className="w-4 h-4" />,
      action: () => { navigate('/profile'); close() },
    },
  ]

  const classroomActions: Action[] = (classrooms as any[]).map((c: any) => ({
    id: `classroom-${c.classroom?.id ?? c.id}`,
    label: c.classroom?.name ?? c.name,
    sublabel: c.classroom ? `${c.classroom.subject_code} · ${c.classroom.section}` : undefined,
    icon: <BookOpen className="w-4 h-4 text-accent" />,
    action: () => { navigate(`/classrooms/${c.classroom?.id ?? c.id}`); close() },
  }))

  const allActions = [...staticActions, ...classroomActions]
  const filtered = query
    ? allActions.filter(a => fuzzyMatch(a.label + ' ' + (a.sublabel || ''), query))
    : allActions

  useEffect(() => { setSelected(0) }, [query])

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, filtered.length - 1)) }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)) }
    if (e.key === 'Enter' && filtered[selected]) { filtered[selected].action() }
  }

  if (!commandPaletteOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4"
      onClick={close}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Palette */}
      <div
        className="relative w-full max-w-lg gradient-border rounded-2xl shadow-modal overflow-hidden animate-slide-up bg-bg-surface/95 backdrop-blur-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/8">
          <Search className="w-4 h-4 text-zinc-500 flex-shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Search pages, classrooms, actions…"
            className="flex-1 bg-transparent text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none"
          />
          {query && (
            <button onClick={() => setQuery('')} className="text-zinc-600 hover:text-zinc-400">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <kbd className="text-[10px] font-mono text-zinc-600 bg-white/5 border border-white/10 rounded px-1.5 py-0.5">ESC</kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto py-1.5">
          {filtered.length === 0 ? (
            <p className="text-sm text-zinc-600 text-center py-8">No results for &quot;{query}&quot;</p>
          ) : (
            filtered.map((action, i) => (
              <button
                key={action.id}
                onClick={action.action}
                onMouseEnter={() => setSelected(i)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                  i === selected ? 'bg-accent/10 text-zinc-100' : 'text-zinc-400 hover:bg-white/4'
                }`}
              >
                <span className={i === selected ? 'text-accent' : 'text-zinc-600'}>{action.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{action.label}</p>
                  {action.sublabel && <p className="text-xs text-zinc-600 truncate">{action.sublabel}</p>}
                </div>
                {i === selected && (
                  <kbd className="text-[10px] font-mono text-zinc-600 bg-white/5 border border-white/10 rounded px-1.5 py-0.5 flex-shrink-0">↵</kbd>
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
