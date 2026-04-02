'use client'

import { useState } from 'react'
import { Listing } from '@/types/listing'
import ListingCard from './ListingCard'

type ViewMode = 'box' | 'mini' | 'row'

export default function ListingsView({ listings }: { listings: Listing[] }) {
  const [view, setView] = useState<ViewMode>('box')

  return (
    <>
      {/* Toggle */}
      <div className="flex justify-end mb-3">
        <div className="join">
          <button
            className={`join-item btn btn-xs gap-1 ${view === 'box' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setView('box')}
            title="4 boxy na řádek"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            Boxy
          </button>
          <button
            className={`join-item btn btn-xs gap-1 ${view === 'mini' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setView('mini')}
            title="6 miniboxů na řádek"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm6 0a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V4zm6 0a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm6 0a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-3zm6 0a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-3z" />
            </svg>
            Mini
          </button>
          <button
            className={`join-item btn btn-xs gap-1 ${view === 'row' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setView('row')}
            title="Řádkový výpis"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
            Řádky
          </button>
        </div>
      </div>

      {/* Grid */}
      {view === 'box' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {listings.map((l) => <ListingCard key={l.id} listing={l} variant="box" />)}
        </div>
      )}
      {view === 'mini' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2">
          {listings.map((l) => <ListingCard key={l.id} listing={l} variant="mini" />)}
        </div>
      )}
      {view === 'row' && (
        <div className="flex flex-col gap-1">
          {listings.map((l) => <ListingCard key={l.id} listing={l} variant="row" />)}
        </div>
      )}
    </>
  )
}
