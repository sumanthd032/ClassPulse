import client from './client'
import type { FileUploadResponse } from '@/types'

export const filesApi = {
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post<FileUploadResponse>('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: e => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    }).then(r => r.data)
  },

  getUrl: (fileId: string) => `/api/v1/files/${fileId}`,
}
