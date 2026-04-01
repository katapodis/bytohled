'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import {
  getKrajeWithCities,
  getOkresyWithCities,
  getCitiesForOkres,
} from '@/lib/geo'

const SOURCES = [
  { value: 'sreality',     label: 'Sreality' },
  { value: 'bezrealitky',  label: 'Bezrealitky' },
  { value: 'bazos',        label: 'Bazoš' },
]

const DISPOSITIONS = ['1+kk', '1+1', '2+kk', '2+1', '3+kk', '3+1', '4+kk', '4+1']

function parseMulti(raw: string | null): string[] {
  return raw ? raw.split(',').filter(Boolean) : []
}

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

  const push = useCallback((next: URLSearchParams) => {
    next.delete('page')
    router.push(`/listings?${next.toString()}`)
  }, [router])

  const updateFilter = useCallback((key: string, value: string) => {
    const next = new URLSearchParams(params.toString())
    if (value) next.set(key, value)
    else next.delete(key)
    push(next)
  }, [params, push])

  // Multi-toggle: přepne jednu hodnotu v comma-separated parametru
  const toggleMulti = useCallback((key: string, value: string) => {
    const current = parseMulti(params.get(key))
    const next = new URLSearchParams(params.toString())
    const updated = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value]
    if (updated.length > 0) next.set(key, updated.join(','))
    else next.delete(key)
    push(next)
  }, [params, push])

  const handleKrajChange = useCallback((kraj: string) => {
    const next = new URLSearchParams(params.toString())
    if (kraj) next.set('kraj', kraj)
    else next.delete('kraj')
    next.delete('okres')
    next.delete('city')
    push(next)
  }, [params, push])

  const handleOkresChange = useCallback((okres: string) => {
    const next = new URLSearchParams(params.toString())
    if (okres) next.set('okres', okres)
    else next.delete('okres')
    next.delete('city')
    push(next)
  }, [params, push])

  const selectedKraj = params.get('kraj') || ''
  const selectedOkres = params.get('okres') || ''
  const selectedCity = params.get('city') || ''
  const selectedSources = parseMulti(params.get('sources'))
  const selectedDispositions = parseMulti(params.get('dispositions'))

  const availableKraje = getKrajeWithCities(availableCities)
  const availableOkresy = selectedKraj ? getOkresyWithCities(selectedKraj, availableCities) : []
  const citiesForOkres =
    selectedKraj && selectedOkres
      ? getCitiesForOkres(selectedKraj, selectedOkres).filter((c) => availableCities.includes(c))
      : []

  const activeCount = [
    params.get('price_type'),
    params.get('sources'),
    params.get('dispositions'),
    params.get('min_price'),
    params.get('max_price'),
    params.get('kraj'),
    params.get('okres'),
    params.get('city'),
    params.get('only_active'),
    params.get('only_favorites'),
  ].filter(Boolean).length

  const sel = 'select select-bordered select-sm text-sm w-full'

  return (
    <div className="card bg-base-100 shadow-sm mb-5">
      <div className="card-body p-3 flex flex-row flex-wrap items-center gap-2">

        {/* Typ */}
        <select
          value={params.get('price_type') || ''}
          onChange={(e) => updateFilter('price_type', e.target.value)}
          className={sel}
          style={{ width: '120px' }}
        >
          <option value="">Typ</option>
          <option value="sale">Prodej</option>
          <option value="rent">Pronájem</option>
        </select>

        <div className="divider divider-horizontal mx-0 h-8" />

        {/* Zdroje – toggle chips */}
        <div className="flex items-center gap-1 flex-wrap">
          <span className="text-xs text-base-content/50 mr-0.5">Zdroj:</span>
          {SOURCES.map(({ value, label }) => {
            const active = selectedSources.includes(value)
            return (
              <button
                key={value}
                onClick={() => toggleMulti('sources', value)}
                className={`btn btn-xs rounded-full transition-all ${active ? 'btn-primary' : 'btn-outline btn-neutral opacity-60 hover:opacity-100'}`}
              >
                {active && <span className="mr-0.5">✓</span>}
                {label}
              </button>
            )
          })}
        </div>

        <div className="divider divider-horizontal mx-0 h-8" />

        {/* Dispozice – dropdown s checkboxy */}
        <details className="dropdown">
          <summary className={`${sel} cursor-pointer list-none`} style={{ width: '150px' }}>
            Dispozice
            {selectedDispositions.length > 0 && (
              <span className="badge badge-primary badge-xs ml-1">{selectedDispositions.length}</span>
            )}
          </summary>
          <ul className="dropdown-content z-20 menu p-2 shadow-lg bg-base-100 border border-base-200 rounded-box mt-1 w-36 grid grid-cols-2 gap-0.5">
            {DISPOSITIONS.map((d) => {
              const active = selectedDispositions.includes(d)
              return (
                <li key={d}>
                  <label className="flex items-center gap-2 cursor-pointer py-1 px-2 rounded hover:bg-base-200">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggleMulti('dispositions', d)}
                      className="checkbox checkbox-primary checkbox-xs"
                    />
                    <span className="text-sm font-medium">{d}</span>
                  </label>
                </li>
              )
            })}
          </ul>
        </details>

        <div className="divider divider-horizontal mx-0 h-8" />

        {/* Cena */}
        <input
          type="number" placeholder="Cena od" min={0}
          value={params.get('min_price') || ''}
          onChange={(e) => updateFilter('min_price', e.target.value)}
          className="input input-bordered input-sm text-sm"
          style={{ width: '110px' }}
        />
        <span className="text-base-content/40">–</span>
        <input
          type="number" placeholder="Cena do" min={0}
          value={params.get('max_price') || ''}
          onChange={(e) => updateFilter('max_price', e.target.value)}
          className="input input-bordered input-sm text-sm"
          style={{ width: '110px' }}
        />

        <div className="divider divider-horizontal mx-0 h-8" />

        {/* Lokalita */}
        <select value={selectedKraj} onChange={(e) => handleKrajChange(e.target.value)} className={sel} style={{ width: '170px' }}>
          <option value="">Kraj – vše</option>
          {availableKraje.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>

        <select
          value={selectedOkres}
          onChange={(e) => handleOkresChange(e.target.value)}
          disabled={!selectedKraj || availableOkresy.length === 0}
          className={sel}
          style={{ width: '150px' }}
        >
          <option value="">Okres – vše</option>
          {availableOkresy.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>

        <select
          value={selectedCity}
          onChange={(e) => updateFilter('city', e.target.value)}
          disabled={!selectedOkres || citiesForOkres.length === 0}
          className={sel}
          style={{ width: '140px' }}
        >
          <option value="">Město – vše</option>
          {citiesForOkres.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        <div className="divider divider-horizontal mx-0 h-8" />

        {/* Řazení */}
        <select
          value={params.get('sort') || ''}
          onChange={(e) => updateFilter('sort', e.target.value)}
          className={sel}
          style={{ width: '190px' }}
        >
          <option value="">Nejnovější</option>
          <option value="date_asc">Nejstarší</option>
          <option value="price_asc">Cena: od nejnižší</option>
          <option value="price_desc">Cena: od nejvyšší</option>
          <option value="disposition_asc">Dispozice: 1+kk → 4+1</option>
          <option value="disposition_desc">Dispozice: 4+1 → 1+kk</option>
          <option value="city_asc">Lokalita: A → Z</option>
          <option value="city_desc">Lokalita: Z → A</option>
        </select>

        <div className="divider divider-horizontal mx-0 h-8" />

        {/* Checkboxy */}
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={params.get('only_active') === '1'}
            onChange={(e) => updateFilter('only_active', e.target.checked ? '1' : '')}
            className="checkbox checkbox-success checkbox-sm"
          />
          <span className="text-sm">Aktivní</span>
        </label>

        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={params.get('only_favorites') === '1'}
            onChange={(e) => updateFilter('only_favorites', e.target.checked ? '1' : '')}
            className="checkbox checkbox-warning checkbox-sm"
          />
          <span className="text-sm">Oblíbené</span>
        </label>

        {/* Reset */}
        {activeCount > 0 && (
          <>
            <div className="divider divider-horizontal mx-0 h-8" />
            <button
              onClick={() => router.push('/listings')}
              className="btn btn-ghost btn-sm text-error gap-1"
            >
              ✕ Reset
              <span className="badge badge-error badge-sm text-white">{activeCount}</span>
            </button>
          </>
        )}
      </div>
    </div>
  )
}
