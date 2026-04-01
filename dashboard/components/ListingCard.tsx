import Link from 'next/link'
import { Listing } from '@/types/listing'

function formatPrice(price: number | null): string {
  if (!price) return 'Cena neuvedena'
  return `${price.toLocaleString('cs-CZ')} Kč`
}

export default function ListingCard({ listing }: { listing: Listing }) {
  const img = listing.images?.[0]

  return (
    <Link href={`/listing/${listing.id}`} className="block group">
      <div className="card bg-base-100 shadow hover:shadow-lg transition-shadow overflow-hidden h-full">
        {/* Obrázek */}
        <figure className="relative aspect-video overflow-hidden bg-base-200">
          {img ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={img}
              alt={listing.title || ''}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <img src="/placeholder.svg" alt="Bez fotky" className="w-full h-full object-cover" />
          )}
          <div className="absolute top-2 left-2 flex gap-1">
            {!listing.is_active && (
              <span className="badge badge-error badge-sm">Neaktivní</span>
            )}
            {listing.price_type === 'rent' && (
              <span className="badge badge-info badge-sm">Pronájem</span>
            )}
          </div>
          {listing.is_favorite && (
            <span className="absolute top-2 right-2 text-warning text-lg drop-shadow">★</span>
          )}
        </figure>

        <div className="card-body p-3 gap-1">
          <p className="font-semibold text-sm truncate leading-tight">
            {listing.title || '—'}
          </p>
          <p className="text-base font-extrabold text-black">
            {formatPrice(listing.price)}
          </p>
          <div className="flex flex-wrap gap-1 mt-0.5">
            {listing.disposition && (
              <span className="badge badge-secondary badge-sm">{listing.disposition}</span>
            )}
            {listing.area_m2 && (
              <span className="badge badge-accent badge-sm">{listing.area_m2} m²</span>
            )}
          </div>
          {listing.address && (
            <p className="text-xs text-base-content/60 truncate">{listing.address}</p>
          )}
          <p className="text-[10px] text-base-content/40 font-mono mt-0.5">
            {listing.source} · {new Date(listing.first_seen_at).toLocaleDateString('cs-CZ')}
          </p>
        </div>
      </div>
    </Link>
  )
}
