import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { commentsApi } from '@/api/comments'
import { useAuthStore } from '@/stores/authStore'
import { Avatar } from '@/components/ui/Avatar'
import { timeAgo } from '@/lib/utils'
import type { Comment } from '@/types'

interface Props {
  type: 'announcement' | 'assignment'
  targetId: string
}

export function CommentThread({ type, targetId }: Props) {
  const [text, setText] = useState('')
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const queryKey = ['comments', type, targetId]

  const { data: comments = [] } = useQuery({
    queryKey,
    queryFn: () => type === 'announcement'
      ? commentsApi.listForAnnouncement(targetId)
      : commentsApi.listForAssignment(targetId),
  })

  const addMut = useMutation({
    mutationFn: (content: string) => type === 'announcement'
      ? commentsApi.addToAnnouncement(targetId, content)
      : commentsApi.addToAssignment(targetId, content),
    onSuccess: () => {
      setText('')
      qc.invalidateQueries({ queryKey })
    },
    onError: () => toast.error('Failed to post comment'),
  })

  const delMut = useMutation({
    mutationFn: commentsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey }),
    onError: () => toast.error('Failed to delete comment'),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    addMut.mutate(text.trim())
  }

  return (
    <div className="space-y-3">
      {comments.length > 0 && (
        <div className="space-y-2">
          {comments.map((c: Comment) => (
            <div key={c.id} className="flex gap-2.5 group">
              <Avatar name={c.author.full_name} size="xs" />
              <div className="flex-1 min-w-0">
                <div className="bg-bg-elevated rounded-xl px-3 py-2 border border-white/6">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-xs font-semibold text-zinc-300">{c.author.full_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-zinc-600">{timeAgo(c.created_at)}</span>
                      {(user?.id === c.author_id || user?.role === 'teacher' || user?.role === 'admin') && (
                        <button
                          onClick={() => delMut.mutate(c.id)}
                          className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 leading-relaxed">{c.content}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={submit} className="flex gap-2 items-center">
        <Avatar name={user?.full_name || ''} size="xs" />
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Add a comment..."
          className="flex-1 bg-bg-elevated border border-white/8 rounded-xl px-3 py-1.5 text-sm text-zinc-300
                     placeholder:text-zinc-600 focus:outline-none focus:border-accent/40 transition-colors"
          disabled={addMut.isPending}
        />
        <button
          type="submit"
          disabled={!text.trim() || addMut.isPending}
          className="p-1.5 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 disabled:opacity-40 transition-colors"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  )
}
