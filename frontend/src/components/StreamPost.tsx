import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Pin, MoreHorizontal, Pencil, Trash2, MessageSquare, ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'
import { announcementsApi } from '@/api/announcements'
import { useAuthStore } from '@/stores/authStore'
import { Avatar } from '@/components/ui/Avatar'
import { CommentThread } from '@/components/CommentThread'
import { timeAgo } from '@/lib/utils'
import type { Announcement } from '@/types'

interface Props {
  announcement: Announcement
  classroomId: string
  onEdit: (a: Announcement) => void
}

export function StreamPost({ announcement: a, classroomId, onEdit }: Props) {
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [showComments, setShowComments] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  const pinMut = useMutation({
    mutationFn: () => announcementsApi.update(a.id, { pinned: !a.pinned }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['announcements', classroomId] })
      toast.success(a.pinned ? 'Unpinned' : 'Pinned!')
    },
  })

  const delMut = useMutation({
    mutationFn: () => announcementsApi.delete(a.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['announcements', classroomId] })
      toast.success('Announcement deleted')
    },
    onError: () => toast.error('Failed to delete'),
  })

  return (
    <div className={`bg-bg-surface border rounded-2xl overflow-hidden transition-all ${
      a.pinned ? 'border-accent/30 shadow-glow-sm' : 'border-white/6'
    }`}>
      {a.pinned && (
        <div className="flex items-center gap-1.5 px-4 pt-2.5 pb-0">
          <Pin className="w-3 h-3 text-accent fill-accent" />
          <span className="text-[10px] font-semibold text-accent uppercase tracking-wider">Pinned</span>
        </div>
      )}

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5">
            <Avatar name={a.author.full_name} size="sm" />
            <div>
              <p className="text-sm font-semibold text-zinc-200">{a.author.full_name}</p>
              <p className="text-[11px] text-zinc-600">{timeAgo(a.created_at)}</p>
            </div>
          </div>

          {isTeacher && (
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1.5 rounded-lg hover:bg-white/6 text-zinc-600 hover:text-zinc-400 transition-colors"
              >
                <MoreHorizontal className="w-4 h-4" />
              </button>
              {showMenu && (
                <div className="absolute right-0 top-8 z-10 bg-bg-elevated border border-white/10 rounded-xl shadow-modal py-1 min-w-[140px] animate-fade-in">
                  <button
                    onClick={() => { onEdit(a); setShowMenu(false) }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-zinc-100"
                  >
                    <Pencil className="w-3.5 h-3.5" /> Edit
                  </button>
                  <button
                    onClick={() => { pinMut.mutate(); setShowMenu(false) }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-zinc-100"
                  >
                    <Pin className="w-3.5 h-3.5" /> {a.pinned ? 'Unpin' : 'Pin'}
                  </button>
                  <button
                    onClick={() => { if (window.confirm('Delete this announcement?')) delMut.mutate(); setShowMenu(false) }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Content */}
        <h3 className="text-base font-semibold text-zinc-100 mb-1.5">{a.title}</h3>
        <p className="text-sm text-zinc-400 leading-relaxed whitespace-pre-wrap">{a.content}</p>

        {/* Footer */}
        <div className="flex items-center gap-4 mt-4 pt-3 border-t border-white/4">
          <button
            onClick={() => setShowComments(!showComments)}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            {a.comment_count} comment{a.comment_count !== 1 ? 's' : ''}
            <ChevronDown className={`w-3 h-3 transition-transform ${showComments ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Comments */}
      {showComments && (
        <div className="px-4 pb-4 border-t border-white/4 pt-3">
          <CommentThread type="announcement" targetId={a.id} />
        </div>
      )}
    </div>
  )
}
