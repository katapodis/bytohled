'use client'

import { useState } from 'react'

export default function FavoriteButton({ listingId, initial }: { listingId: string; initial: boolean }) {
  const [isFavorite, setIsFavorite] = useState(initial)
  const [loading, setLoading] = useState(false)

  async function toggle() {
    setLoading(true)
    const res = await fetch(`/api/listing/${listingId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_favorite: !isFavorite }),
    })
    if (res.ok) setIsFavorite(!isFavorite)
    setLoading(false)
  }

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className={`text-3xl transition-transform hover:scale-110 disabled:opacity-50 ${isFavorite ? 'text-yellow-400' : 'text-gray-300'}`}
      title={isFavorite ? 'Odebrat z oblíbených' : 'Přidat do oblíbených'}
    >
      ★
    </button>
  )
}
