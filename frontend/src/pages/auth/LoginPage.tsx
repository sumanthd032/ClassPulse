import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Zap, Sparkles, ShieldCheck, Gauge } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const { login, isLoggingIn } = useAuth()
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  return (
    <div className="min-h-screen bg-bg-base relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-24 left-10 w-64 h-64 bg-violet-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-16 right-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl" />
      </div>

      <div className="relative min-h-screen grid grid-cols-1 lg:grid-cols-2">
        <div className="hidden lg:flex items-center justify-center px-12">
          <div className="max-w-md">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-zinc-300 text-xs mb-6">
              <Sparkles className="w-3.5 h-3.5 text-violet-300" />
              AI-powered classroom workflow
            </div>
            <h1 className="text-4xl font-bold text-zinc-100 leading-tight">
              Teach faster. Learn better. All in one modern workspace.
            </h1>
            <p className="text-zinc-400 mt-4">
              ClassPulse helps students iterate with instant AI feedback while teachers grade with confidence.
            </p>
            <div className="mt-8 grid gap-3">
              <div className="flex items-center gap-3 text-sm text-zinc-300">
                <Gauge className="w-4 h-4 text-emerald-400" /> Real-time dashboards
              </div>
              <div className="flex items-center gap-3 text-sm text-zinc-300">
                <ShieldCheck className="w-4 h-4 text-blue-400" /> Plagiarism and grading safeguards
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center p-4 sm:p-8">
          <div className="w-full max-w-sm">
            <div className="flex items-center justify-center gap-2.5 mb-8">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-accent to-violet-400 flex items-center justify-center shadow-glow">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-zinc-100 tracking-tight">ClassPulse</span>
            </div>

            <div className="bg-bg-surface/90 border border-white/10 rounded-2xl p-8 shadow-modal backdrop-blur-xl">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-zinc-100">Welcome back</h2>
                <p className="text-sm text-zinc-500 mt-1">Sign in to your account</p>
              </div>

              <form onSubmit={handleSubmit(data => login(data))} className="space-y-4">
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
                  placeholder="••••••••"
                  error={errors.password?.message}
                  {...register('password')}
                />
                <Button type="submit" className="w-full" loading={isLoggingIn} size="md">
                  Sign in
                </Button>
              </form>

              <p className="text-sm text-zinc-500 text-center mt-5">
                Don't have an account?{' '}
                <Link to="/register" className="text-accent hover:text-accent/80 transition-colors font-medium">
                  Create one
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
