export type JobStatus =
  | 'queued'
  | 'downloading'
  | 'converting'
  | 'completed'
  | 'failed'

export interface Job {
  id: string
  url: string
  bitrate: string
  status: JobStatus
  title: string | null
  uploader: string | null
  duration: number | null
  thumbnail_url: string | null
  progress: number
  speed: string | null
  eta: number | null
  error: string | null
  created_at: string
  updated_at: string
}

export interface VideoInfo {
  title: string | null
  uploader: string | null
  duration: number | null
  thumbnail: string | null
  webpage_url: string | null
}

const RAW_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const BASE = RAW_BASE.replace(/\/+$/, '')

const TARGET = BASE || 'mismo origen (falta VITE_API_BASE_URL)'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new Error(
      `No se pudo conectar con la API en ${TARGET}. Revisa VITE_API_BASE_URL y el CORS.`,
    )
  }

  const text = await res.text()
  let data: unknown
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    const detail =
      data && typeof data === 'object' && 'detail' in data
        ? (data as { detail: unknown }).detail
        : text || res.statusText || `HTTP ${res.status}`
    throw new Error(
      typeof detail === 'string' ? detail : JSON.stringify(detail),
    )
  }

  if (res.status === 204 || text === '') return undefined as T
  return data as T
}

export const api = {
  createJobs: (urls: string[], bitrate: string) =>
    request<Job[]>('/api/v1/jobs', {
      method: 'POST',
      body: JSON.stringify({ urls, bitrate }),
    }),
  listJobs: () => request<Job[]>('/api/v1/jobs'),
  getJob: (id: string) => request<Job>(`/api/v1/jobs/${id}`),
  deleteJob: (id: string) =>
    request<void>(`/api/v1/jobs/${id}`, { method: 'DELETE' }),
  downloadUrl: (id: string) => `${BASE}/api/v1/jobs/${id}/download`,
  eventsUrl: (id: string) => `${BASE}/api/v1/jobs/${id}/events`,
}
