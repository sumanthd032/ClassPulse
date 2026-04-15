import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Users, Hash, Copy, Check } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { classroomsApi } from '@/api/classrooms'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Card, SkeletonCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import type { Enrollment } from '@/types'

// ---- Create Classroom Modal ----
const createSchema = z.object({
  name: z.string().min(3, 'Name is required'),
  subject_code: z.string().min(2, 'Subject code is required'),
  section: z.string().min(1, 'Section is required'),
  semester: z.string().min(1, 'Semester is required'),
})
type CreateForm = z.infer<typeof createSchema>

function CreateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, reset, formState: { errors } } = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
  })
  const mutation = useMutation({
    mutationFn: classroomsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['classrooms'] })
      toast.success('Classroom created!')
      reset()
      onClose()
    },
    onError: () => toast.error('Failed to create classroom'),
  })
  return (
    <Modal open={open} onClose={onClose} title="New Classroom" size="sm">
      <form onSubmit={handleSubmit(d => mutation.mutate(d))} className="space-y-4">
        <Input label="Classroom name" placeholder="Intro to CS" error={errors.name?.message} {...register('name')} />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Subject code" placeholder="CS101" error={errors.subject_code?.message} {...register('subject_code')} />
          <Input label="Section" placeholder="A" error={errors.section?.message} {...register('section')} />
        </div>
        <Input label="Semester" placeholder="Spring 2026" error={errors.semester?.message} {...register('semester')} />
        <Button type="submit" className="w-full" loading={mutation.isPending}>Create classroom</Button>
      </form>
    </Modal>
  )
}

// ---- Join Classroom Modal ----
const joinSchema = z.object({ join_code: z.string().length(6, 'Join code must be 6 characters') })
type JoinForm = z.infer<typeof joinSchema>

function JoinModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, reset, formState: { errors } } = useForm<JoinForm>({
    resolver: zodResolver(joinSchema),
  })
  const mutation = useMutation({
    mutationFn: ({ join_code }: JoinForm) => classroomsApi.join(join_code),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['classrooms'] })
      toast.success('Joined classroom!')
      reset()
      onClose()
    },
    onError: () => toast.error('Invalid join code'),
  })
  return (
    <Modal open={open} onClose={onClose} title="Join a Classroom" size="sm">
      <form onSubmit={handleSubmit(d => mutation.mutate(d))} className="space-y-4">
        <Input
          label="Join code"
          placeholder="ABC123"
          hint="Ask your teacher for the 6-character code"
          error={errors.join_code?.message}
          {...register('join_code')}
        />
        <Button type="submit" className="w-full" loading={mutation.isPending}>Join classroom</Button>
      </form>
    </Modal>
  )
}

// ---- Classroom Card ----
function ClassroomCard({ enrollment }: { enrollment: Enrollment }) {
  const { classroom } = enrollment
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)

  const copy = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(classroom.join_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card hover onClick={() => navigate(`/classrooms/${classroom.id}`)}>
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent/30 to-violet-600/20 flex items-center justify-center text-base font-bold text-accent">
          {classroom.subject_code.slice(0, 2)}
        </div>
        <Badge variant="muted">{enrollment.role === 'co_teacher' ? 'Co-teacher' : 'Student'}</Badge>
      </div>
      <h3 className="font-semibold text-zinc-100 text-sm leading-snug mb-1">{classroom.name}</h3>
      <p className="text-xs text-zinc-500">{classroom.subject_code} · {classroom.section} · {classroom.semester}</p>
      <div className="mt-4 pt-3 border-t border-white/6 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-zinc-500 text-xs">
          <Hash className="w-3 h-3" />
          <span className="font-mono tracking-wider">{classroom.join_code}</span>
        </div>
        <button onClick={copy} className="p-1 rounded-lg hover:bg-white/8 text-zinc-600 hover:text-zinc-300 transition-colors">
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      </div>
    </Card>
  )
}

// ---- Page ----
export default function ClassroomsPage() {
  const { user } = useAuthStore()
  const [createOpen, setCreateOpen] = useState(false)
  const [joinOpen, setJoinOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['classrooms'],
    queryFn: classroomsApi.list,
  })

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-zinc-100">Classrooms</h2>
          <p className="text-sm text-zinc-500 mt-0.5">
            {isTeacher ? 'Manage your classes' : 'Your enrolled classes'}
          </p>
        </div>
        <div className="flex gap-2">
          {!isTeacher && (
            <Button variant="ghost" size="sm" onClick={() => setJoinOpen(true)}>
              <Users className="w-4 h-4 mr-1.5" /> Join
            </Button>
          )}
          {isTeacher && (
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" /> New Classroom
            </Button>
          )}
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : !data?.length ? (
        <EmptyState
          icon={<BookOpenIcon />}
          title={isTeacher ? 'No classrooms yet' : 'Not enrolled yet'}
          description={isTeacher ? 'Create your first classroom to get started.' : 'Ask your teacher for a join code.'}
          action={
            isTeacher
              ? <Button size="sm" onClick={() => setCreateOpen(true)}><Plus className="w-4 h-4 mr-1.5" /> New Classroom</Button>
              : <Button variant="ghost" size="sm" onClick={() => setJoinOpen(true)}><Users className="w-4 h-4 mr-1.5" /> Join a Classroom</Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map(e => <ClassroomCard key={e.classroom_id} enrollment={e} />)}
        </div>
      )}

      <CreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <JoinModal open={joinOpen} onClose={() => setJoinOpen(false)} />
    </div>
  )
}

function BookOpenIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>
}
