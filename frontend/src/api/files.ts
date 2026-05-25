import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
})

export const filesApi = {
  upload: async (file: File): Promise<{ file_id: string; url: string; filename: string; size: number; mime_type: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  delete: async (fileId: string) => {
    return api.delete(`/files/${fileId}`)
  },
}
