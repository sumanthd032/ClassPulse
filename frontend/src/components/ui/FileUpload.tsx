import { useRef, useState } from 'react'
import { Upload, X } from 'lucide-react'
import { Button } from './Button'
import toast from 'react-hot-toast'
import { filesApi } from '@/api/files'

const ALLOWED_TYPES = {
  'application/pdf': '.pdf',
  'application/msword': '.doc',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt',
  'image/jpeg': '.jpg',
  'image/png': '.png',
  'image/gif': '.gif',
  'image/webp': '.webp',
  'application/zip': '.zip',
  'application/x-zip-compressed': '.zip',
}

interface FileUploadProps {
  onUpload: (file: { file_id: string; url: string; filename: string; size: number }) => void
  maxSizeMb?: number
  accept?: string
  label?: string
}

export function FileUpload({ onUpload, maxSizeMb = 50, accept = Object.values(ALLOWED_TYPES).join(','), label = 'Choose file' }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate type
    if (!ALLOWED_TYPES[file.type as keyof typeof ALLOWED_TYPES]) {
      toast.error(`File type not allowed. Allowed: ${Object.values(ALLOWED_TYPES).join(', ')}`)
      return
    }

    // Validate size
    const maxSizeBytes = maxSizeMb * 1024 * 1024
    if (file.size > maxSizeBytes) {
      toast.error(`File too large. Max: ${maxSizeMb}MB`)
      return
    }

    setLoading(true)
    try {
      const uploaded = await filesApi.upload(file)
      onUpload({
        file_id: uploaded.file_id,
        url: uploaded.url,
        filename: uploaded.filename,
        size: uploaded.size,
      })
      toast.success('File uploaded!')
      if (inputRef.current) inputRef.current.value = ''
    } catch (err) {
      toast.error('Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        hidden
        onChange={handleUpload}
        accept={accept}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        loading={loading}
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="w-3.5 h-3.5 mr-1.5" />
        {label}
      </Button>
    </div>
  )
}
