import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Calendar, Users, ChevronRight, BookOpen,
  Lock, Globe, Copy, Check, Hash, ClipboardList,
  Megaphone, Package, ExternalLink, Trash2, Link2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { classroomsApi } from '@/api/classrooms'
import { assignmentsApi } from '@/api/assignments'
import { announcementsApi } from '@/api/announcements'
import { materialsApi } from '@/api/materials'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { Card, SkeletonCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { EmptyState } from '@/components/ui/EmptyState'
import { StreamPost } from '@/components/StreamPost'
import { formatDate, deadlineLabel, isPastDeadline } from '@/lib/utils'
import type { Assignment, Announcement, Material } from '@/types'

// Palette of header gradients
const CLASSROOM_GRADIENTS = [
  'from-violet-600 to-blue-600',
  'from-emerald-600 to-teal-600',
  'from-orange-600 to-red-600',
  'from-pink-600 to-violet-600',
  'from-blue-600 to-cyan-600',
  'from-amber-600 to-orange-600',
]

function getGradient(id: string) {
  const idx = parseInt(id.replace(/-/g, '').slice(0, 8), 16) % CLASSROOM_GRADIENTS.length
  return CLASSROOM_GRADIENTS[idx]
}

function PublishToggle({ a }: { a: Assignment }) {
  const qc = useQueryClient()
  const { id } = useParams<{ id: string }>()
  const mutation = useMutation({
    mutationFn: () => assignmentsApi.update(a.id, { is_published: !a.is_published }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assignments', id] })
      toast.success(a.is_published ? 'Unpublished' : 'Published!')
    },
    onError: () => toast.error('Failed to update'),
  })
  return (
    <button
      onClick={e => { e.stopPropagation(); mutation.mutate() }}
      disabled={mutation.isPending}
      title={a.is_published ? 'Click to unpublish' : 'Click to publish'}
      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
        a.is_published
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
          : 'border-white/10 bg-white/5 text-zinc-500 hover:text-zinc-300 hover:border-white/20'
      }`}
    >
      {mutation.isPending ? '…' : a.is_published ? '● Published' : '○ Draft'}
    </button>
  )
}

function AssignmentRow({ a, onClick, isTeacher }: { a: Assignment; onClick: () => void; isTeacher: boolean }) {
  const isPast = isPastDeadline(a.deadline)
  const daysUntil = isPast ? -1 : (new Date(a.deadline).getTime() - Date.now()) / 86_400_000
  const dlVariant = isPast ? 'danger' : daysUntil < 1 ? 'warning' : daysUntil < 3 ? 'blue' : 'muted'

  const handleRowClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    onClick()
  }

  return (
    <div
      onClick={handleRowClick}
      className="w-full flex items-center gap-4 px-4 py-3.5 hover:bg-white/3 transition-colors group text-left border-b border-white/4 last:border-0 cursor-pointer"
    >
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
        a.is_published ? 'bg-accent/10 text-accent' : 'bg-white/5 text-zinc-600'
      }`}>
        {a.is_published ? <Globe className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-zinc-200 truncate">{a.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-zinc-600 flex items-center gap-1">
            <Calendar className="w-3 h-3" /> {formatDate(a.deadline)}
          </span>
          <span className="text-zinc-700">·</span>
          <span className="text-xs text-zinc-600">{a.total_marks} pts</span>
          {a.criteria.length > 0 && (
            <>
              <span className="text-zinc-700">·</span>
              <span className="text-xs text-zinc-600">{a.criteria.length} criteria</span>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <Badge variant={dlVariant} className="text-[10px]">{deadlineLabel(a.deadline)}</Badge>
        {isTeacher && <PublishToggle a={a} />}
        <ChevronRight className="w-4 h-4 text-zinc-700 group-hover:text-zinc-400 transition-colors" />
      </div>
    </div>
  )
}

// ---- Stream Tab ----
function StreamTab({ classroomId, isTeacher }: { classroomId: string; isTeacher: boolean }) {
  const qc = useQueryClient()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')

  const { data: announcements = [], isLoading } = useQuery({
    queryKey: ['announcements', classroomId],
    queryFn: () => announcementsApi.list(classroomId),
  })

  const createMut = useMutation({
    mutationFn: () => announcementsApi.create(classroomId, { title: title.trim(), content: content.trim() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['announcements', classroomId] })
      setTitle('')
      setContent('')
      toast.success('Announcement posted!')
    },
    onError: () => toast.error('Failed to post announcement'),
  })

  const updateMut = useMutation({
    mutationFn: () => announcementsApi.update(editingAnnouncement!.id, { title: editTitle.trim(), content: editContent.trim() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['announcements', classroomId] })
      setEditingAnnouncement(null)
      toast.success('Announcement updated!')
    },
    onError: () => toast.error('Failed to update'),
  })

  const handleEdit = (a: Announcement) => {
    setEditingAnnouncement(a)
    setEditTitle(a.title)
    setEditContent(a.content)
  }

  // Sort: pinned first, then by date desc
  const sorted = [...announcements].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1
    if (!a.pinned && b.pinned) return 1
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })

  return (
    <div className="space-y-4">
      {/* Create announcement form (teacher only) */}
      {isTeacher && (
        <div className="bg-bg-surface border border-white/6 rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
            <Megaphone className="w-4 h-4 text-accent" /> Post Announcement
          </h3>
          <div className="space-y-2">
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Title"
              className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40 transition-colors"
            />
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Share something with your class…"
              rows={3}
              className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40 resize-none transition-colors"
            />
            <div className="flex justify-end">
              <Button
                size="sm"
                onClick={() => createMut.mutate()}
                loading={createMut.isPending}
                disabled={!title.trim() || !content.trim()}
              >
                Post
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editingAnnouncement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4" onClick={() => setEditingAnnouncement(null)}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <div className="relative bg-bg-surface border border-white/10 rounded-2xl p-5 w-full max-w-lg shadow-modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-sm font-semibold text-zinc-200 mb-3">Edit Announcement</h3>
            <div className="space-y-2">
              <input
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-accent/40"
              />
              <textarea
                value={editContent}
                onChange={e => setEditContent(e.target.value)}
                rows={4}
                className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 resize-none focus:outline-none focus:border-accent/40"
              />
              <div className="flex justify-end gap-2">
                <Button variant="ghost" size="sm" onClick={() => setEditingAnnouncement(null)}>Cancel</Button>
                <Button size="sm" onClick={() => updateMut.mutate()} loading={updateMut.isPending}>Save</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Announcements list */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(2)].map((_, i) => <div key={i} className="skeleton h-32 rounded-2xl" />)}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<Megaphone className="w-6 h-6" />}
          title="No announcements yet"
          description={isTeacher ? 'Post the first announcement for this class.' : 'Your teacher hasn\'t posted any announcements yet.'}
        />
      ) : (
        sorted.map(a => (
          <StreamPost
            key={a.id}
            announcement={a}
            classroomId={classroomId}
            onEdit={handleEdit}
          />
        ))
      )}
    </div>
  )
}

// ---- Materials Tab ----
function MaterialsTab({ classroomId, isTeacher }: { classroomId: string; isTeacher: boolean }) {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [matTitle, setMatTitle] = useState('')
  const [matType, setMatType] = useState<'link' | 'file' | 'video' | 'document'>('link')
  const [matUrl, setMatUrl] = useState('')
  const [matDesc, setMatDesc] = useState('')

  const { data: materials = [], isLoading } = useQuery({
    queryKey: ['materials', classroomId],
    queryFn: () => materialsApi.list(classroomId),
  })

  const createMut = useMutation({
    mutationFn: () => materialsApi.create(classroomId, {
      title: matTitle.trim(),
      material_type: matType,
      url: matUrl.trim() || undefined,
      description: matDesc.trim() || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['materials', classroomId] })
      setShowForm(false)
      setMatTitle('')
      setMatUrl('')
      setMatDesc('')
      setMatType('link')
      toast.success('Material added!')
    },
    onError: () => toast.error('Failed to add material'),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => materialsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['materials', classroomId] })
      toast.success('Material removed')
    },
    onError: () => toast.error('Failed to remove material'),
  })

  const typeIcon = (type: string) => {
    if (type === 'link') return <Link2 className="w-4 h-4" />
    if (type === 'video') return <ExternalLink className="w-4 h-4" />
    return <Package className="w-4 h-4" />
  }

  return (
    <div className="space-y-4">
      {isTeacher && (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setShowForm(v => !v)} variant={showForm ? 'ghost' : 'primary'}>
            <Plus className="w-4 h-4 mr-1.5" /> {showForm ? 'Cancel' : 'Add Material'}
          </Button>
        </div>
      )}

      {showForm && (
        <div className="bg-bg-surface border border-white/6 rounded-2xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-zinc-300">New Material</h3>
          <input
            value={matTitle}
            onChange={e => setMatTitle(e.target.value)}
            placeholder="Title"
            className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40"
          />
          <select
            value={matType}
            onChange={e => setMatType(e.target.value as any)}
            className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-accent/40"
          >
            <option value="link">Link</option>
            <option value="file">File</option>
            <option value="video">Video</option>
            <option value="document">Document</option>
          </select>
          <input
            value={matUrl}
            onChange={e => setMatUrl(e.target.value)}
            placeholder="URL (optional)"
            className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40"
          />
          <textarea
            value={matDesc}
            onChange={e => setMatDesc(e.target.value)}
            placeholder="Description (optional)"
            rows={2}
            className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40 resize-none"
          />
          <div className="flex justify-end">
            <Button size="sm" onClick={() => createMut.mutate()} loading={createMut.isPending} disabled={!matTitle.trim()}>
              Add Material
            </Button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}
        </div>
      ) : materials.length === 0 ? (
        <EmptyState
          icon={<Package className="w-6 h-6" />}
          title="No materials yet"
          description={isTeacher ? 'Add links, files, and resources for your students.' : 'Your teacher hasn\'t added any materials yet.'}
        />
      ) : (
        <div className="bg-bg-surface border border-white/6 rounded-2xl overflow-hidden divide-y divide-white/4">
          {materials.map((m: Material) => (
            <div key={m.id} className="flex items-center gap-3 px-4 py-3 hover:bg-white/2 transition-colors group">
              <div className="w-8 h-8 rounded-lg bg-accent/10 text-accent flex items-center justify-center flex-shrink-0">
                {typeIcon(m.material_type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-200 truncate">{m.title}</p>
                {m.description && <p className="text-xs text-zinc-600 truncate">{m.description}</p>}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="chip border-white/8 text-zinc-500 capitalize">{m.material_type}</span>
                {m.url && (
                  <a
                    href={m.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 rounded-lg hover:bg-white/6 text-zinc-600 hover:text-zinc-300 transition-colors"
                    onClick={e => e.stopPropagation()}
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
                {isTeacher && (
                  <button
                    onClick={() => { if (window.confirm('Remove this material?')) deleteMut.mutate(m.id) }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/10 text-zinc-600 hover:text-red-400 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ClassroomDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [tab, setTab] = useState<'stream' | 'assignments' | 'materials' | 'people'>('stream')
  const [copied, setCopied] = useState(false)

  const {
    data: classroom,
    isLoading: loadingClass,
    isError: classroomError,
    error: classroomErrorObj,
  } = useQuery({
    queryKey: ['classroom', id],
    queryFn: () => classroomsApi.get(id!),
    enabled: !!id,
  })

  const {
    data: assignments = [],
    isLoading: loadingAssignments,
    isError: assignmentsError,
    error: assignmentsErrorObj,
    refetch: refetchAssignments,
  } = useQuery({
    queryKey: ['assignments', id],
    queryFn: () => assignmentsApi.list(id!),
    enabled: !!id,
  })

  const { data: students = [], isLoading: loadingStudents } = useQuery({
    queryKey: ['students', id],
    queryFn: () => classroomsApi.students(id!),
    enabled: !!id && tab === 'people' && isTeacher,
  })

  const copyCode = () => {
    if (!classroom) return
    navigator.clipboard.writeText(classroom.join_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loadingClass) {
    return (
      <div className="max-w-3xl space-y-4">
        <div className="skeleton h-36 rounded-2xl" />
        <SkeletonCard />
      </div>
    )
  }

  if (classroomError) {
    const status = (classroomErrorObj as any)?.response?.status
    const msg =
      status === 403
        ? 'You are not enrolled in this classroom.'
        : status === 422
          ? 'Invalid classroom link. Open the class from the Classrooms page.'
          : 'Failed to load classroom details.'
    return (
      <Card>
        <p className="text-sm text-zinc-300">{msg}</p>
      </Card>
    )
  }

  if (!classroom) return <p className="text-zinc-500">Classroom not found.</p>

  const gradient = getGradient(classroom.id)
  const published = assignments.filter(a => a.is_published).length
  const drafts = assignments.filter(a => !a.is_published).length

  const tabs = [
    { key: 'stream' as const, label: 'Stream', icon: <Megaphone className="w-3.5 h-3.5" /> },
    { key: 'assignments' as const, label: 'Assignments', icon: <ClipboardList className="w-3.5 h-3.5" /> },
    { key: 'materials' as const, label: 'Materials', icon: <Package className="w-3.5 h-3.5" /> },
    ...(isTeacher ? [{ key: 'people' as const, label: 'People', icon: <Users className="w-3.5 h-3.5" /> }] : []),
  ]

  return (
    <div className="max-w-3xl space-y-4">
      {/* Classroom header banner */}
      <div className={`relative rounded-2xl bg-gradient-to-br ${gradient} p-6 overflow-hidden`}>
        <div className="absolute inset-0 bg-black/20" />
        <div className="relative">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-white/70 text-xs font-mono font-semibold">{classroom.subject_code}</span>
                <span className="text-white/40">·</span>
                <span className="text-white/70 text-xs">{classroom.section}</span>
                <span className="text-white/40">·</span>
                <span className="text-white/70 text-xs">{classroom.semester}</span>
              </div>
              <h2 className="text-xl font-bold text-white">{classroom.name}</h2>
            </div>
            {isTeacher && (
              <Button
                size="sm"
                onClick={() => navigate(`/classrooms/${id}/assignments/new`)}
                className="bg-white/15 hover:bg-white/25 text-white border-white/20 border backdrop-blur"
                variant="ghost"
              >
                <Plus className="w-4 h-4 mr-1.5" /> New Assignment
              </Button>
            )}
          </div>

          <div className="flex items-center gap-4 mt-4">
            <button
              onClick={copyCode}
              className="flex items-center gap-2 bg-black/20 hover:bg-black/30 transition-colors rounded-xl px-3 py-1.5 border border-white/10"
            >
              <Hash className="w-3.5 h-3.5 text-white/70" />
              <span className="text-white font-mono text-sm font-semibold tracking-widest">{classroom.join_code}</span>
              {copied
                ? <Check className="w-3.5 h-3.5 text-emerald-300" />
                : <Copy className="w-3.5 h-3.5 text-white/50" />
              }
            </button>
            <span className="text-white/50 text-xs">Click to copy join code</span>
          </div>
        </div>
      </div>

      {/* Stats row (teacher) */}
      {isTeacher && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-bg-surface border border-white/6 rounded-xl px-4 py-3 text-center">
            <p className="text-xl font-bold text-zinc-100">{students.length || '—'}</p>
            <p className="text-xs text-zinc-500 mt-0.5">Students</p>
          </div>
          <div className="bg-bg-surface border border-white/6 rounded-xl px-4 py-3 text-center">
            <p className="text-xl font-bold text-emerald-400">{published}</p>
            <p className="text-xs text-zinc-500 mt-0.5">Published</p>
          </div>
          <div className="bg-bg-surface border border-white/6 rounded-xl px-4 py-3 text-center">
            <p className="text-xl font-bold text-zinc-400">{drafts}</p>
            <p className="text-xs text-zinc-500 mt-0.5">Drafts</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-bg-elevated p-1 rounded-xl w-fit border border-white/6 flex-wrap">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              tab === t.key
                ? 'bg-bg-surface text-zinc-200 shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      {/* Stream tab */}
      {tab === 'stream' && (
        <StreamTab classroomId={id!} isTeacher={isTeacher} />
      )}

      {/* Assignments */}
      {tab === 'assignments' && (
        <div className="bg-bg-surface border border-white/6 rounded-2xl overflow-hidden">
          {loadingAssignments ? (
            <div className="p-4 space-y-3">
              {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}
            </div>
          ) : assignmentsError ? (
            <EmptyState
              icon={<Lock className="w-6 h-6" />}
              title="Can’t load assignments"
              description={
                (assignmentsErrorObj as any)?.response?.status === 403
                  ? 'You are not enrolled in this classroom yet. Join the class to see assignments.'
                  : 'Something went wrong while loading assignments.'
              }
              action={(
                <Button size="sm" variant="outline" onClick={() => refetchAssignments()}>
                  Retry
                </Button>
              )}
            />
          ) : !assignments.length ? (
            <EmptyState
              icon={<BookOpen className="w-6 h-6" />}
              title="No assignments yet"
              description={
                isTeacher
                  ? 'Create the first assignment for this class. Draft assignments are visible only to teachers.'
                  : 'No published assignments yet. Draft assignments are hidden until your teacher publishes them.'
              }
              action={isTeacher ? (
                <Button size="sm" onClick={() => navigate(`/classrooms/${id}/assignments/new`)}>
                  <Plus className="w-4 h-4 mr-1.5" /> New Assignment
                </Button>
              ) : undefined}
            />
          ) : (
            <div>
              {assignments.map(a => (
                <AssignmentRow
                  key={a.id}
                  a={a}
                  isTeacher={isTeacher}
                  onClick={() => navigate(`/assignments/${a.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Materials tab */}
      {tab === 'materials' && (
        <MaterialsTab classroomId={id!} isTeacher={isTeacher} />
      )}

      {/* People (teacher only) */}
      {tab === 'people' && isTeacher && (
        <div className="bg-bg-surface border border-white/6 rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-white/6 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-300">Students ({students.length})</h3>
          </div>
          {loadingStudents ? (
            <div className="p-4 space-y-3">
              {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-12 rounded-xl" />)}
            </div>
          ) : !students.length ? (
            <EmptyState
              icon={<Users className="w-6 h-6" />}
              title="No students enrolled"
              description={`Share the join code  ${classroom.join_code}  with students.`}
            />
          ) : (
            <div className="divide-y divide-white/4">
              {students.map((s, i) => (
                <div key={s.user_id} className="flex items-center gap-3 px-4 py-3 hover:bg-white/2 transition-colors">
                  <span className="text-xs text-zinc-700 w-5 text-right">{i + 1}</span>
                  <Avatar name={s.full_name} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-300">{s.full_name}</p>
                    <p className="text-xs text-zinc-600">{s.email}</p>
                  </div>
                  <span className="text-xs text-zinc-600 flex items-center gap-1">
                    <Calendar className="w-3 h-3" /> Joined {formatDate(s.joined_at)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
