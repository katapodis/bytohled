import Link from 'next/link'
import { Listing } from '@/types/listing'

function formatPrice(price: number | null): string {
  if (!price) return 'Cena neuvedena'
  return `${price.toLocaleString('cs-CZ')} Kč`
}

export default function ListingCard({ listing }: { listing: Listing }) {
  const img = listing.images?.[0]

  return (
    <Link href={`/listing/${listing.id}`} className="block bg-white rounded-xl shadow hover:shadow-md transition-shadow overflow-hidden">
      <div className="aspect-video bg-gray-100 relative">
        {img ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={img} alt={listing.title || ''} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">Bez fotky</div>
        )}
        {!listing.is_active && (
          <span className="absolute top-2 left-2 bg-red-500 text-white text-xs px-2 py-1 rounded">Neaktivní</span>
        )}
        {listing.is_favorite && (
          <span className="absolute top-2 right-2 text-yellow-400 text-lg">★</span>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 truncate">{listing.title}</h3>
        <p className="text-blue-600 font-bold mt-1">{formatPrice(listing.price)}</p>
        <div className="flex gap-2 mt-2 text-sm text-gray-500 flex-wrap">
          {listing.disposition && <span className="bg-gray-100 px-2 py-0.5 rounded">{listing.disposition}</span>}
          {listing.area_m2 && <span className="bg-gray-100 px-2 py-0.5 rounded">{listing.area_m2} m²</span>}
          {listing.price_type === 'rent' && <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">Pronájem</span>}
        </div>
        {listing.address && <p className="text-sm text-gray-500 mt-1 truncate">{listing.address}</p>}
        <p className="text-xs text-gray-400 mt-2">{listing.source} · {new Date(listing.first_seen_at).toLocaleDateString('cs-CZ')}</p>
      </div>
    </Link>
  )
}
