'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

type RunStatus = 'idle' | 'triggering' | 'queued' | 'in_progress' | 'completed' | 'failed' | 'error'

interface Listing {
  id: string
  title: string | null
  price: number | null
  disposition: string | null
  area_m2: number | null
  address: string | null
  images: string[]
  source: string
}

interface Progress {
  addedCount: number
  deactivatedCount: number
  recentListings: Listing[]
}

function formatPrice(price: number | null) {
  if (!price) return null
  return `${price.toLocaleString('cs-CZ')} Kč`
}

const STATUS_LABEL: Record<RunStatus, string> = {
  idle:        '',
  triggering:  'Spouštím...',
  queued:      'Ve frontě...',
  in_progress: 'Probíhá...',
  completed:   'Hotovo',
  failed:      'Selhalo',
  error:       'Chyba',
}

const POLL_STATUS_MS  = 6_000
const POLL_PROGRESS_MS = 8_000

export default function ScrapeButton() {
  const [status, setStatus]       = useState<RunStatus>('idle')
  const [progress, setProgress]   = useState<Progress | null>(null)
  const [triggeredAt, setTriggeredAt] = useState<string | null>(null)
  const [open, setOpen]           = useState(false)

  const statusTimer   = useRef<ReturnType<typeof setInterval> | null>(null)
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const clearTimers = () => {
    if (statusTimer.current)   clearInterval(statusTimer.current)
    if (progressTimer.current) clearInterval(progressTimer.current)
  }

  const fetchProgress = useCallback(async (since: string) => {
    const res = await fetch(`/api/scrape/progress?since=${encodeURIComponent(since)}`)
    if (res.ok) {
      const data = await res.json()
      setProgress(data)
    }
  }, [])

  const pollStatus = useCallback(async (since: string) => {
    const res = await fetch(`/api/scrape/status?since=${encodeURIComponent(since)}`)
    if (!res.ok) return
    const { status: s } = await res.json()
    setStatus(s as RunStatus)
    if (s === 'completed' || s === 'failed') {
      clearTimers()
      await fetchProgress(since)
    }
  }, [fetchProgress])

  const startPolling = useCallback((since: string) => {
    clearTimers()
    statusTimer.current   = setInterval(() => pollStatus(since), POLL_STATUS_MS)
    progressTimer.current = setInterval(() => fetchProgress(since), POLL_PROGRESS_MS)
  }, [pollStatus, fetchProgress])

  async function trigger() {
    setStatus('triggering')
    setProgress(null)
    setOpen(true)

    const res = await fetch('/api/scrape', { method: 'POST' })
    const data = await res.json()

    if (!res.ok) {
      setStatus('error')
      return
    }

    const since = data.triggeredAt as string
    setTriggeredAt(since)
    setStatus('queued')
    startPolling(since)
  }

  function reset() {
    clearTimers()
    setStatus('idle')
    setProgress(null)
    setTriggeredAt(null)
    setOpen(false)
  }

  useEffect(() => () => clearTimers(), [])

  const running = status === 'queued' || status === 'in_progress' || status === 'triggering'
  const done    = status === 'completed' || status === 'failed' || status === 'error'

  const btnColor =
    done && status !== 'completed' ? 'btn-error' :
    status === 'completed'         ? 'btn-success' :
    'btn-primary'

  const accentBorder =
    done && status !== 'completed' ? 'border-error' :
    status === 'completed'         ? 'border-success' :
    'border-primary'

  return (
    <div className="relative">
      {/* Tlačítko */}
      {status === 'idle' ? (
        <button onClick={trigger} className="btn btn-sm btn-primary gap-1.5">
          ▶ Spustit scraping
        </button>
      ) : (
        <button
          onClick={() => setOpen((o) => !o)}
          className={`btn btn-sm gap-1.5 ${btnColor} ${open ? 'rounded-b-none' : ''}`}
        >
          {running && <span className="loading loading-spinner loading-xs" />}
          {STATUS_LABEL[status]}
          {open ? '▲' : '▼'}
        </button>
      )}

      {/* Panel — připojený k tlačítku bez mezery, se sdíleným rohem */}
      {open && status !== 'idle' && (
        <div className={`absolute right-0 top-full z-50 w-80 bg-base-100 shadow-xl border border-base-200 rounded-lg rounded-tr-none border-t-2 ${accentBorder}`}>
          <div className="p-4 flex flex-col gap-3">

            {/* Progress bar */}
            {running && (
              <progress className="progress progress-primary w-full" />
            )}

            {/* Statistiky */}
            {progress && (
              <div className="flex gap-3">
                <div className="flex-1 bg-success/10 rounded-lg p-2 text-center">
                  <p className="text-lg font-extrabold text-success">+{progress.addedCount}</p>
                  <p className="text-[10px] text-base-content/50 uppercase tracking-wide">přidáno</p>
                </div>
                <div className="flex-1 bg-error/10 rounded-lg p-2 text-center">
                  <p className="text-lg font-extrabold text-error">{progress.deactivatedCount}</p>
                  <p className="text-[10px] text-base-content/50 uppercase tracking-wide">deaktivováno</p>
                </div>
              </div>
            )}

            {/* Live feed nových inzerátů */}
            {progress && progress.recentListings.length > 0 && (
              <div>
                <p className="text-[10px] text-base-content/40 uppercase tracking-wide mb-1.5">Nové inzeráty</p>
                <div className="flex flex-col gap-1.5">
                  {progress.recentListings.map((l) => (
                    <a
                      key={l.id}
                      href={`/listing/${l.id}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-2 hover:bg-base-200 rounded-lg p-1.5 transition-colors"
                    >
                      <div className="w-10 h-8 flex-shrink-0 rounded overflow-hidden bg-base-200">
                        {l.images?.[0]
                          ? <img src={l.images[0]} alt="" className="w-full h-full object-cover" />
                          : <div className="w-full h-full bg-base-300" />
                        }
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{l.title || '—'}</p>
                        <p className="text-[10px] text-base-content/50 truncate">
                          {[l.disposition, l.area_m2 ? `${l.area_m2} m²` : null, formatPrice(l.price)]
                            .filter(Boolean).join(' · ')}
                        </p>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Running – zatím žádná data */}
            {running && !progress && (
              <p className="text-xs text-base-content/40 text-center">Čekám na data...</p>
            )}

            {/* Zavřít / Reset */}
            {done && (
              <button onClick={reset} className="btn btn-ghost btn-xs w-full mt-1">
                Zavřít
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
