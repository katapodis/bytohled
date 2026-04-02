'use client'

import { useState, useEffect, useCallback } from 'react'

interface ScrapeLog {
  id: string
  scraped_at: string
  added_count: number
  deactivated_count: number
}

interface ApiResponse {
  data: ScrapeLog[]
  count: number
  page: number
  perPage: number
}

export default function ScrapeLogModal() {
  const [open, setOpen] = useState(false)
  const [logs, setLogs] = useState<ScrapeLog[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [loading, setLoading] = useState(false)

  const perPage = 20
  const totalPages = Math.ceil(count / perPage)

  const fetchLogs = useCallback(async (p: number, from: string, to: string) => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(p) })
    if (from) params.set('date_from', from)
    if (to) params.set('date_to', to)
    const res = await fetch(`/api/scrape-logs?${params}`)
    const json: ApiResponse = await res.json()
    setLogs(json.data || [])
    setCount(json.count || 0)
    setLoading(false)
  }, [])

  useEffect(() => {
    if (open) fetchLogs(page, dateFrom, dateTo)
  }, [open, page, dateFrom, dateTo, fetchLogs])

  function applyFilter() {
    setPage(1)
    fetchLogs(1, dateFrom, dateTo)
  }

  function resetFilter() {
    setDateFrom('')
    setDateTo('')
    setPage(1)
    fetchLogs(1, '', '')
  }

  return (
    <>
      <button
        className="text-[10px] text-base-content/40 hover:text-base-content/70 underline underline-offset-2 transition-colors"
        onClick={() => setOpen(true)}
      >
        Historie scrapingu
      </button>

      {open && (
        <div className="modal modal-open">
          <div className="modal-box max-w-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">Historie scrapingu</h3>
              <button className="btn btn-sm btn-circle btn-ghost" onClick={() => setOpen(false)}>✕</button>
            </div>

            {/* Filtrace */}
            <div className="flex flex-wrap gap-2 items-end mb-4">
              <div>
                <label className="text-xs text-base-content/60 block mb-1">Od</label>
                <input
                  type="date"
                  className="input input-sm input-bordered"
                  value={dateFrom}
                  onChange={e => setDateFrom(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-base-content/60 block mb-1">Do</label>
                <input
                  type="date"
                  className="input input-sm input-bordered"
                  value={dateTo}
                  onChange={e => setDateTo(e.target.value)}
                />
              </div>
              <button className="btn btn-sm btn-primary" onClick={applyFilter}>Filtrovat</button>
              {(dateFrom || dateTo) && (
                <button className="btn btn-sm btn-ghost" onClick={resetFilter}>Resetovat</button>
              )}
              <span className="text-xs text-base-content/40 ml-auto">{count} záznamů</span>
            </div>

            {/* Tabulka */}
            <div className="overflow-x-auto">
              <table className="table table-sm w-full">
                <thead>
                  <tr>
                    <th>Datum a čas</th>
                    <th className="text-success text-center">+ Přidáno</th>
                    <th className="text-error text-center">✕ Deaktivováno</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={3} className="text-center py-6">
                        <span className="loading loading-spinner loading-sm" />
                      </td>
                    </tr>
                  )}
                  {!loading && logs.length === 0 && (
                    <tr>
                      <td colSpan={3} className="text-center py-6 text-base-content/40 text-sm">
                        Žádné záznamy
                      </td>
                    </tr>
                  )}
                  {!loading && logs.map(log => (
                    <tr key={log.id}>
                      <td className="font-mono text-xs">
                        {new Date(log.scraped_at).toLocaleString('cs-CZ', {
                          day: '2-digit', month: '2-digit', year: 'numeric',
                          hour: '2-digit', minute: '2-digit',
                        })}
                      </td>
                      <td className="text-center">
                        <span className={`font-semibold text-sm ${log.added_count > 0 ? 'text-success' : 'text-base-content/30'}`}>
                          {log.added_count > 0 ? `+${log.added_count}` : '—'}
                        </span>
                      </td>
                      <td className="text-center">
                        <span className={`font-semibold text-sm ${log.deactivated_count > 0 ? 'text-error' : 'text-base-content/30'}`}>
                          {log.deactivated_count > 0 ? log.deactivated_count : '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Stránkování */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2 mt-4">
                <button
                  className="btn btn-xs btn-outline"
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                >←</button>
                <span className="text-xs text-base-content/50 tabular-nums">{page} / {totalPages}</span>
                <button
                  className="btn btn-xs btn-outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >→</button>
              </div>
            )}
          </div>
          <div className="modal-backdrop" onClick={() => setOpen(false)} />
        </div>
      )}
    </>
  )
}
