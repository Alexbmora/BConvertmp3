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

const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      if (data?.detail) {
        detail =
          typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail)
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
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
