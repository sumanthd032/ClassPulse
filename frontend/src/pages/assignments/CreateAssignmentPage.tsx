import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Plus, Trash2, GripVertical } from 'lucide-react'
import toast from 'react-hot-toast'
import { assignmentsApi } from '@/api/assignments'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'

const criterionSchema = z.object({
  name: z.string().min(1, 'Criterion name required'),
  max_marks: z.coerce.number().min(1, 'Min 1'),
  levels: z.object({
    excellent: z.string().optional(),
    good: z.string().optional(),
    average: z.string().optional(),
    poor: z.string().optional(),
  }),
})

const schema = z.object({
  title: z.string().min(3, 'Title is required'),
  description: z.string().optional(),
  deadline: z.string().min(1, 'Deadline is required'),
  total_marks: z.coerce.number().min(1),
  submission_type: z.enum(['text', 'file', 'both']),
  max_drafts: z.coerce.number().min(1).max(10),
  late_policy: z.enum(['block', 'penalty', 'allow']),
  penalty_per_day: z.coerce.number().min(0).optional(),
  is_published: z.boolean(),
  criteria: z.array(criterionSchema).min(1, 'Add at least one criterion'),
}).superRefine((data, ctx) => {
  const sum = data.criteria.reduce((acc, c) => acc + (Number(c.max_marks) || 0), 0)
  if (sum !== data.total_marks) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['criteria'],
      message: `Criteria marks sum (${sum}) must equal total marks (${data.total_marks})`,
    })
  }
})
type FormData = z.infer<typeof schema>

export default function CreateAssignmentPage() {
  const { id: classroomId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [expandedCriterion, setExpandedCriterion] = useState<number | null>(0)

  const { register, handleSubmit, control, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      submission_type: 'text',
      max_drafts: 3,
      late_policy: 'allow',
      is_published: true,
      total_marks: 100,
      criteria: [{ name: '', max_marks: 10, levels: {} }],
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'criteria' })
  const latePolicy = watch('late_policy')
  const isPublished = watch('is_published')
  const watchedCriteria = watch('criteria')
  const watchedTotal = watch('total_marks')
  const allocatedMarks = watchedCriteria?.reduce((acc, c) => acc + (Number(c.max_marks) || 0), 0) ?? 0
  const remainingMarks = (Number(watchedTotal) || 0) - allocatedMarks

  const mutation = useMutation({
    mutationFn: (data: FormData) => assignmentsApi.create(classroomId!, {
      ...data,
      criteria: data.criteria.map((c, i) => ({
        ...c,
        levels: Object.fromEntries(Object.entries(c.levels).filter(([, v]) => v)),
      })),
    }),
    onSuccess: (a) => {
      toast.success('Assignment created!')
      navigate(`/assignments/${a.id}`)
    },
    onError: () => toast.error('Failed to create assignment'),
  })

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-zinc-100">New Assignment</h2>
        <p className="text-sm text-zinc-500 mt-0.5">Configure details and build the grading rubric</p>
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} className="space-y-5">
        {/* Basic info */}
        <Card>
          <h3 className="text-sm font-semibold text-zinc-300 mb-4">Assignment Details</h3>
          <div className="space-y-4">
            <Input label="Title" placeholder="Essay: Climate Change" {...register('title')} error={errors.title?.message} />
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Description (optional)</label>
              <textarea
                placeholder="Instructions, resources, expectations…"
                rows={3}
                className="w-full bg-bg-elevated border border-white/8 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 resize-none focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 transition-all"
                {...register('description')}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input label="Deadline" type="datetime-local" {...register('deadline')} error={errors.deadline?.message} />
              <Input label="Total marks" type="number" {...register('total_marks')} error={errors.total_marks?.message} />
            </div>
          </div>
        </Card>

        {/* Submission settings */}
        <Card>
          <h3 className="text-sm font-semibold text-zinc-300 mb-4">Submission Settings</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Submission type</label>
              <select
                className="w-full bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-accent/40"
                {...register('submission_type')}
              >
                <option value="text">Text</option>
                <option value="file">File upload</option>
                <option value="both">Text + File</option>
              </select>
            </div>
            <Input label="Max drafts" type="number" min={1} max={10} {...register('max_drafts')} error={errors.max_drafts?.message} />
          </div>
          <div className="mt-4">
            <label className="block text-xs font-medium text-zinc-400 mb-1.5">Late policy</label>
            <div className="flex gap-2">
              {(['block', 'penalty', 'allow'] as const).map(p => (
                <label
                  key={p}
                  className={`flex-1 flex items-center justify-center px-3 py-2 rounded-xl border cursor-pointer text-xs font-medium transition-all ${
                    latePolicy === p
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-white/8 bg-white/3 text-zinc-500 hover:border-white/15'
                  }`}
                >
                  <input type="radio" value={p} {...register('late_policy')} className="sr-only" />
                  {p === 'block' ? '🚫 Block' : p === 'penalty' ? '📉 Penalty' : '✅ Allow'}
                </label>
              ))}
            </div>
            {latePolicy === 'penalty' && (
              <div className="mt-3">
                <Input label="Penalty per day (%)" type="number" min={0} max={100} {...register('penalty_per_day')} />
              </div>
            )}
          </div>
          <div className="mt-4 flex items-center justify-between rounded-xl border border-white/10 bg-bg-elevated/70 px-3 py-2.5">
            <div>
              <p className="text-sm font-medium text-zinc-200">Publish immediately</p>
              <p className="text-xs text-zinc-500">
                {isPublished ? 'Students can see this assignment right after creation.' : 'Saved as draft. Students will not see it until published.'}
              </p>
            </div>
            <label className="inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only" {...register('is_published')} />
              <span className={`h-6 w-11 rounded-full border transition-colors ${isPublished ? 'bg-emerald-500/30 border-emerald-500/40' : 'bg-white/10 border-white/20'}`}>
                <span className={`block h-5 w-5 rounded-full bg-white mt-0.5 transition-transform ${isPublished ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </span>
            </label>
          </div>
        </Card>

        {/* Rubric builder */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-300">Grading Rubric</h3>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                append({ name: '', max_marks: 10, levels: {} })
                setExpandedCriterion(fields.length)
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add criterion
            </Button>
          </div>

          {errors.criteria?.root && (
            <p className="text-xs text-red-400 mb-3">{errors.criteria.root.message}</p>
          )}
          <p className={`text-xs mb-3 ${remainingMarks === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
            Allocated: {allocatedMarks}/{watchedTotal || 0} marks
            {remainingMarks !== 0 ? ` (${remainingMarks > 0 ? `${remainingMarks} remaining` : `${Math.abs(remainingMarks)} over`})` : ''}
          </p>

          <div className="space-y-2">
            {fields.map((field, i) => (
              <div key={field.id} className="border border-white/8 rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedCriterion(expandedCriterion === i ? null : i)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-white/4 transition-colors text-left"
                >
                  <GripVertical className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                  <span className="flex-1 text-sm text-zinc-300">
                    {watch(`criteria.${i}.name`) || <span className="text-zinc-600 italic">Untitled criterion</span>}
                  </span>
                  <span className="text-xs text-zinc-600">{watch(`criteria.${i}.max_marks`)} pts</span>
                  <button
                    type="button"
                    onClick={e => { e.stopPropagation(); remove(i) }}
                    className="p-1 rounded-lg hover:bg-red-500/10 text-zinc-600 hover:text-red-400 transition-colors ml-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </button>

                {expandedCriterion === i && (
                  <div className="px-4 pb-4 pt-0 space-y-3 border-t border-white/6">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="col-span-2">
                        <Input
                          label="Criterion name"
                          placeholder="e.g. Argument Quality"
                          {...register(`criteria.${i}.name`)}
                          error={(errors.criteria?.[i]?.name as any)?.message}
                        />
                      </div>
                      <Input
                        label="Max marks"
                        type="number"
                        {...register(`criteria.${i}.max_marks`)}
                        error={(errors.criteria?.[i]?.max_marks as any)?.message}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {(['excellent', 'good', 'average', 'poor'] as const).map(level => (
                        <Input
                          key={level}
                          label={level.charAt(0).toUpperCase() + level.slice(1)}
                          placeholder={`Describe ${level} performance…`}
                          {...register(`criteria.${i}.levels.${level}`)}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Submit */}
        <div className="flex gap-3 justify-end">
          <Button type="button" variant="ghost" onClick={() => navigate(-1)}>Cancel</Button>
          <Button type="submit" loading={mutation.isPending}>Create Assignment</Button>
        </div>
      </form>
    </div>
  )
}
