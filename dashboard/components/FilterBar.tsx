'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import {
  getKrajeWithCities,
  getOkresyWithCities,
  getCitiesForOkres,
} from '@/lib/geo'

export default function FilterBar() {
  const router = useRouter()
  const params = useSearchParams()
  const [availableCities, setAvailableCities] = useState<string[]>([])

  useEffect(() => {
    fetch('/api/locations')
      .then((r) => r.json())
      .then((cities: string[]) => setAvailableCities(cities))
      .catch(() => {})
  }, [])

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

  const selectedKraj = params.get('kraj') || ''
  const selectedOkres = params.get('okres') || ''
  const selectedCity = params.get('city') || ''

  const availableKraje = getKrajeWithCities(availableCities)
  const availableOkresy = selectedKraj ? getOkresyWithCities(selectedKraj, availableCities) : []
  const citiesForOkres = selectedKraj && selectedOkres
    ? getCitiesForOkres(selectedKraj, selectedOkres).filter((c) => availableCities.includes(c))
    : []

  const handleKrajChange = useCallback((kraj: string) => {
    const next = new URLSearchParams(params.toString())
    next.delete('page')
    if (kraj) {
      next.set('kraj', kraj)
    } else {
      next.delete('kraj')
    }
    next.delete('okres')
    next.delete('city')
    router.push(`/listings?${next.toString()}`)
  }, [params, router])

  const handleOkresChange = useCallback((okres: string) => {
    const next = new URLSearchParams(params.toString())
    next.delete('page')
    if (okres) {
      next.set('okres', okres)
    } else {
      next.delete('okres')
    }
    next.delete('city')
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

      {availableKraje.length > 0 && (
        <select
          value={selectedKraj}
          onChange={(e) => handleKrajChange(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Kraj (vše)</option>
          {availableKraje.map((k) => (
            <option key={k} value={k}>{k}</option>
          ))}
        </select>
      )}

      {selectedKraj && availableOkresy.length > 0 && (
        <select
          value={selectedOkres}
          onChange={(e) => handleOkresChange(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Okres (vše)</option>
          {availableOkresy.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      )}

      {selectedOkres && citiesForOkres.length > 0 && (
        <select
          value={selectedCity}
          onChange={(e) => updateFilter('city', e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Město (vše)</option>
          {citiesForOkres.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      )}

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
