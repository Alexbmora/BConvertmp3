import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type Job } from './lib/api'

const BITRATES = ['128', '192', '256', '320']

const STATUS_LABEL: Record<Job['status'], string> = {
  queued: 'En cola',
  downloading: 'Descargando',
  converting: 'Convirtiendo',
  completed: 'Listo',
  failed: 'Error',
}

const STATUS_COLOR: Record<Job['status'], string> = {
  queued: 'bg-slate-600',
  downloading: 'bg-sky-500',
  converting: 'bg-amber-500',
  completed: 'bg-emerald-500',
  failed: 'bg-rose-500',
}

function isActive(job: Job) {
  return job.status !== 'completed' && job.status !== 'failed'
}

function formatDuration(seconds: number | null) {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function App() {
  const [input, setInput] = useState('')
  const [bitrate, setBitrate] = useState('192')
  const [jobs, setJobs] = useState<Job[]>([])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const refresh = useCallback(async () => {
    try {
      setJobs(await api.listJobs())
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const hasActive = useMemo(() => jobs.some(isActive), [jobs])

  useEffect(() => {
    if (!hasActive) return
    const id = setInterval(() => void refresh(), 1500)
    return () => clearInterval(id)
  }, [hasActive, refresh])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const urls = input
      .split(/[\s,]+/)
      .map((url) => url.trim())
      .filter(Boolean)
    if (urls.length === 0) {
      setError('Pega al menos una URL de YouTube')
      return
    }
    setSubmitting(true)
    try {
      const created = await api.createJobs(urls, bitrate)
      setJobs((prev) => [...created, ...prev])
      setInput('')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.deleteJob(id)
      setJobs((prev) => prev.filter((job) => job.id !== id))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">
            YouTube <span className="text-rose-500">→</span> MP3
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Pega una o varias URLs (una por línea) y descarga el audio en MP3.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-5"
        >
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={'https://www.youtube.com/watch?v=...\nhttps://youtu.be/...'}
            rows={4}
            className="w-full resize-y rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm outline-none focus:border-rose-500"
          />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-300">
              Bitrate
              <select
                value={bitrate}
                onChange={(event) => setBitrate(event.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-rose-500"
              >
                {BITRATES.map((value) => (
                  <option key={value} value={value}>
                    {value} kbps
                  </option>
                ))}
              </select>
            </label>

            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-rose-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-rose-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? 'Enviando…' : 'Convertir'}
            </button>
          </div>

          {error && (
            <p className="rounded-lg bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
              {error}
            </p>
          )}
        </form>

        <section className="mt-8 space-y-3">
          {jobs.length === 0 && (
            <p className="text-center text-sm text-slate-500">
              Aún no hay conversiones.
            </p>
          )}

          {jobs.map((job) => (
            <article
              key={job.id}
              className="flex gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4"
            >
              <div className="h-16 w-24 shrink-0 overflow-hidden rounded-lg bg-slate-800">
                {job.thumbnail_url && (
                  <img
                    src={job.thumbnail_url}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                )}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <p className="truncate text-sm font-medium">
                    {job.title ?? job.url}
                  </p>
                  <button
                    type="button"
                    onClick={() => void handleDelete(job.id)}
                    className="shrink-0 text-xs text-slate-500 hover:text-rose-400"
                  >
                    Eliminar
                  </button>
                </div>

                <p className="mt-0.5 truncate text-xs text-slate-500">
                  {job.uploader ?? '—'} · {formatDuration(job.duration)} ·{' '}
                  {job.bitrate} kbps
                </p>

                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full transition-all ${STATUS_COLOR[job.status]}`}
                    style={{
                      width: `${job.status === 'completed' ? 100 : job.progress}%`,
                    }}
                  />
                </div>

                <div className="mt-2 flex items-center justify-between gap-2 text-xs">
                  <span className="text-slate-400">
                    {STATUS_LABEL[job.status]}
                    {job.status === 'downloading' && job.speed
                      ? ` · ${job.speed}`
                      : ''}
                    {job.status === 'failed' && job.error
                      ? ` · ${job.error}`
                      : ''}
                  </span>

                  {job.status === 'completed' ? (
                    <a
                      href={api.downloadUrl(job.id)}
                      className="rounded-md bg-emerald-600 px-3 py-1 font-medium text-white hover:bg-emerald-500"
                    >
                      Descargar MP3
                    </a>
                  ) : (
                    <span className="text-slate-500">
                      {Math.round(job.progress)}%
                    </span>
                  )}
                </div>
              </div>
            </article>
          ))}
        </section>
      </div>
    </div>
  )
}
