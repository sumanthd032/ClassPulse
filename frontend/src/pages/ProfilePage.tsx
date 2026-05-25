import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { User, KeyRound, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { FileUpload } from '@/components/ui/FileUpload'
import { useState } from 'react'

const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  avatar_url: z.string().url('Must be a valid URL').or(z.literal('')).optional(),
})

const passwordSchema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, {
  message: "Passwords don't match",
  path: ['confirm'],
})

type ProfileForm = z.infer<typeof profileSchema>
type PasswordForm = z.infer<typeof passwordSchema>

export default function ProfilePage() {
  const { user, setUser } = useAuthStore()
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? '')

  const { register: regP, handleSubmit: handleP, formState: { errors: errP }, setValue } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: user?.full_name ?? '', avatar_url: user?.avatar_url ?? '' },
  })

  const { register: regPw, handleSubmit: handlePw, reset: resetPw, formState: { errors: errPw } } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  })

  const profileMutation = useMutation({
    mutationFn: (data: ProfileForm) => authApi.updateProfile(data),
    onSuccess: updated => {
      setUser(updated)
      toast.success('Profile updated!')
    },
    onError: () => toast.error('Failed to update profile'),
  })

  const passwordMutation = useMutation({
    mutationFn: ({ password }: PasswordForm) => authApi.updateProfile({ password }),
    onSuccess: () => {
      toast.success('Password changed!')
      resetPw()
    },
    onError: () => toast.error('Failed to change password'),
  })

  const handleAvatarUpload = (file: any) => {
    setAvatarUrl(file.url)
    setValue('avatar_url', file.url)
  }

  if (!user) return null

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h2 className="text-xl font-bold text-zinc-100">Profile</h2>
        <p className="text-sm text-zinc-500 mt-0.5">Manage your account details</p>
      </div>

      {/* Current profile */}
      <Card>
        <div className="flex items-center gap-4 mb-6">
          <Avatar name={user.full_name} size="lg" src={avatarUrl} />
          <div>
            <p className="font-semibold text-zinc-200">{user.full_name}</p>
            <p className="text-sm text-zinc-500">{user.email}</p>
            <Badge variant="purple" className="mt-1 capitalize">{user.role}</Badge>
          </div>
        </div>

        <form onSubmit={handleP(d => profileMutation.mutate(d))} className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-400 flex items-center gap-2">
            <User className="w-4 h-4" /> Personal Info
          </h3>
          <Input
            label="Full name"
            error={errP.full_name?.message}
            {...regP('full_name')}
          />
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-2">Avatar</label>
            <div className="flex items-center gap-2">
              <FileUpload
                onUpload={handleAvatarUpload}
                maxSizeMb={5}
                accept=".jpg,.jpeg,.png,.gif,.webp"
                label="Upload picture"
              />
              <span className="text-xs text-zinc-500">or</span>
              <Input
                placeholder="https://…/avatar.png"
                className="flex-1"
                error={errP.avatar_url?.message}
                {...regP('avatar_url')}
              />
            </div>
          </div>
          <Button type="submit" size="sm" loading={profileMutation.isPending}>
            <Save className="w-3.5 h-3.5 mr-1.5" /> Save changes
          </Button>
        </form>
      </Card>

      {/* Password change */}
      <Card>
        <form onSubmit={handlePw(d => passwordMutation.mutate(d))} className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-400 flex items-center gap-2">
            <KeyRound className="w-4 h-4" /> Change Password
          </h3>
          <Input
            label="New password"
            type="password"
            placeholder="Min. 8 characters"
            error={errPw.password?.message}
            {...regPw('password')}
          />
          <Input
            label="Confirm new password"
            type="password"
            placeholder="Repeat password"
            error={errPw.confirm?.message}
            {...regPw('confirm')}
          />
          <Button type="submit" size="sm" variant="ghost" loading={passwordMutation.isPending}>
            <KeyRound className="w-3.5 h-3.5 mr-1.5" /> Update password
          </Button>
        </form>
      </Card>
    </div>
  )
}
