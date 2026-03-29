'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Listing } from '@/types/listing'
import FavoriteButton from '@/components/FavoriteButton'

function formatPrice(price: number | null): string {
  if (!price) return 'Cena neuvedena'
  return `${price.toLocaleString('cs-CZ')} Kč`
}

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [listing, setListing] = useState<Listing | null>(null)
  const [note, setNote] = useState('')
  const [activeImg, setActiveImg] = useState(0)

  useEffect(() => {
    fetch(`/api/listing/${id}`)
      .then((r) => r.json())
      .then((data: Listing) => {
        setListing(data)
        setNote(data.note || '')
      })
  }, [id])

  const saveNote = useCallback(async () => {
    await fetch(`/api/listing/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note }),
    })
  }, [id, note])

  if (!listing) return <div className="p-8 text-center text-gray-500">Načítám...</div>

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        <Link href="/listings" className="text-blue-600 text-sm hover:underline mb-4 inline-block">← Zpět na seznam</Link>

        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-xl font-bold flex-1 mr-4">{listing.title}</h1>
            <FavoriteButton listingId={listing.id} initial={listing.is_favorite} />
          </div>

          {listing.images.length > 0 && (
            <div className="mb-6">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={listing.images[activeImg]} alt="" className="w-full rounded-lg object-cover max-h-96" />
              {listing.images.length > 1 && (
                <div className="flex gap-2 mt-2 overflow-x-auto">
                  {listing.images.map((img, i) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img key={i} src={img} alt="" onClick={() => setActiveImg(i)}
                      className={`w-16 h-16 object-cover rounded cursor-pointer border-2 ${i === activeImg ? 'border-blue-500' : 'border-transparent'}`} />
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm mb-6">
            <div><span className="text-gray-500">Cena</span><p className="font-bold text-blue-600 text-lg">{formatPrice(listing.price)}</p></div>
            <div><span className="text-gray-500">Typ</span><p>{listing.price_type === 'sale' ? 'Prodej' : 'Pronájem'}</p></div>
            {listing.disposition && <div><span className="text-gray-500">Dispozice</span><p>{listing.disposition}</p></div>}
            {listing.area_m2 && <div><span className="text-gray-500">Plocha</span><p>{listing.area_m2} m²</p></div>}
            {listing.address && <div className="col-span-2"><span className="text-gray-500">Adresa</span><p>{listing.address}</p></div>}
            <div><span className="text-gray-500">Zdroj</span><p>{listing.source}</p></div>
            <div><span className="text-gray-500">Stav</span><p className={listing.is_active ? 'text-green-600' : 'text-red-500'}>{listing.is_active ? 'Aktivní' : 'Neaktivní'}</p></div>
            <div><span className="text-gray-500">Nalezeno</span><p>{new Date(listing.first_seen_at).toLocaleDateString('cs-CZ')}</p></div>
          </div>

          {listing.description && (
            <div className="mb-6">
              <h2 className="font-semibold mb-2">Popis</h2>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{listing.description}</p>
            </div>
          )}

          <div className="mb-6">
            <h2 className="font-semibold mb-2">Poznámka</h2>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onBlur={saveNote}
              placeholder="Vlastní poznámka..."
              className="w-full border rounded-lg px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
            />
          </div>

          <a href={listing.url} target="_blank" rel="noopener noreferrer"
            className="block w-full text-center bg-blue-600 text-white rounded-lg py-3 font-medium hover:bg-blue-700">
            Zobrazit původní inzerát →
          </a>
        </div>
      </div>
    </div>
  )
}
