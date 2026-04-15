import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Zap, Sparkles } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

const schema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  role: z.enum(['student', 'teacher']),
})
type FormData = z.infer<typeof schema>

export default function RegisterPage() {
  const { register: registerUser, isRegistering } = useAuth()
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'student' },
  })

  const selectedRole = watch('role')

  return (
    <div className="min-h-screen bg-bg-base flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-24 left-10 w-64 h-64 bg-violet-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-16 right-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-accent to-violet-400 flex items-center justify-center shadow-glow">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-zinc-100 tracking-tight">ClassPulse</span>
        </div>

        <div className="bg-bg-surface/90 border border-white/10 rounded-2xl p-8 shadow-modal backdrop-blur-xl">
          <div className="mb-6">
            <h1 className="text-lg font-semibold text-zinc-100">Create your account</h1>
            <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-300" /> Get started with ClassPulse
            </p>
          </div>

          <form onSubmit={handleSubmit(data => registerUser(data))} className="space-y-4">
            <Input
              label="Full name"
              placeholder="Jane Smith"
              error={errors.full_name?.message}
              {...register('full_name')}
            />
            <Input
              label="Email"
              type="email"
              placeholder="you@school.edu"
              error={errors.email?.message}
              {...register('email')}
            />
            <Input
              label="Password"
              type="password"
              placeholder="Min. 8 characters"
              error={errors.password?.message}
              {...register('password')}
            />

            {/* Role toggle */}
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-2">I am a</label>
              <div className="grid grid-cols-2 gap-2">
                {(['student', 'teacher'] as const).map(r => (
                  <label
                    key={r}
                    className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border cursor-pointer text-sm font-medium transition-all ${
                      selectedRole === r
                        ? 'border-accent bg-accent/10 text-accent'
                        : 'border-white/8 bg-white/3 text-zinc-500 hover:border-white/15'
                    }`}
                  >
                    <input type="radio" value={r} {...register('role')} className="sr-only" />
                    {r === 'student' ? '🎓' : '👩‍🏫'} {r.charAt(0).toUpperCase() + r.slice(1)}
                  </label>
                ))}
              </div>
            </div>

            <Button type="submit" className="w-full" loading={isRegistering} size="md">
              Create account
            </Button>
          </form>

          <p className="text-sm text-zinc-500 text-center mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-accent hover:text-accent/80 transition-colors font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
