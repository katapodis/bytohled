'use client'

import { useState } from 'react'

type State = 'idle' | 'loading' | 'success' | 'error'

export default function ScrapeButton() {
  const [state, setState] = useState<State>('idle')

  async function trigger() {
    setState('loading')
    try {
      const res = await fetch('/api/scrape', { method: 'POST' })
      if (res.ok) {
        setState('success')
        setTimeout(() => setState('idle'), 3000)
      } else {
        const data = await res.json()
        console.error(data.error)
        setState('error')
        setTimeout(() => setState('idle'), 3000)
      }
    } catch {
      setState('error')
      setTimeout(() => setState('idle'), 3000)
    }
  }

  return (
    <button
      onClick={trigger}
      disabled={state === 'loading'}
      className={`btn btn-sm gap-1.5 ${
        state === 'success' ? 'btn-success' :
        state === 'error'   ? 'btn-error'   :
        'btn-primary'
      }`}
    >
      {state === 'loading' && <span className="loading loading-spinner loading-xs" />}
      {state === 'idle'    && '▶ Spustit scraping'}
      {state === 'loading' && 'Spouštím...'}
      {state === 'success' && '✓ Spuštěno'}
      {state === 'error'   && '✕ Chyba'}
    </button>
  )
}
