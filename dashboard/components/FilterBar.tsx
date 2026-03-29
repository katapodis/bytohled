'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback } from 'react'

export default function FilterBar() {
  const router = useRouter()
  const params = useSearchParams()

  const updateFilter = useCallback((key: string, value: string) => {
    const next = new URLSearchParams(params.toString())
    if (value) {
      next.set(key, value)
    } else {
      next.delete(key)
    }
    next.delete('page')
    router.push(`/listings?${next.toString()}`)
  }, [params, router])

  return (
    <div className="flex flex-wrap gap-3 p-4 bg-white rounded-xl shadow mb-6">
      <select
        value={params.get('price_type') || ''}
        onChange={(e) => updateFilter('price_type', e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm"
      >
        <option value="">Typ (vše)</option>
        <option value="sale">Prodej</option>
        <option value="rent">Pronájem</option>
      </select>

      <select
        value={params.get('source') || ''}
        onChange={(e) => updateFilter('source', e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm"
      >
        <option value="">Zdroj (vše)</option>
        <option value="sreality">Sreality</option>
        <option value="bezrealitky">Bezrealitky</option>
        <option value="bazos">Bazoš</option>
      </select>

      <select
        value={params.get('disposition') || ''}
        onChange={(e) => updateFilter('disposition', e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm"
      >
        <option value="">Dispozice (vše)</option>
        {['1+kk', '1+1', '2+kk', '2+1', '3+kk', '3+1'].map((d) => (
          <option key={d} value={d}>{d}</option>
        ))}
      </select>

      <input
        type="number"
        placeholder="Max. cena (Kč)"
        value={params.get('max_price') || ''}
        onChange={(e) => updateFilter('max_price', e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm w-40"
      />

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={params.get('only_active') === '1'}
          onChange={(e) => updateFilter('only_active', e.target.checked ? '1' : '')}
        />
        Pouze aktivní
      </label>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={params.get('only_favorites') === '1'}
          onChange={(e) => updateFilter('only_favorites', e.target.checked ? '1' : '')}
        />
        Pouze oblíbené
      </label>
    </div>
  )
}
