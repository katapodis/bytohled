import Link from 'next/link'
import { Listing } from '@/types/listing'

type Variant = 'box' | 'mini' | 'row'

function formatPrice(price: number | null): string {
  if (!price) return 'Cena neuvedena'
  return `${price.toLocaleString('cs-CZ')} Kč`
}

export default function ListingCard({ listing, variant = 'box' }: { listing: Listing; variant?: Variant }) {
  const img = listing.images?.[0]

  if (variant === 'row') {
    return (
      <Link href={`/listing/${listing.id}`} className="block group">
        <div className="flex items-center gap-3 bg-base-100 rounded-lg px-3 py-2 hover:shadow transition-shadow">
          <div className="w-16 h-12 flex-shrink-0 rounded overflow-hidden bg-base-200">
            {img
              ? <img src={img} alt="" className="w-full h-full object-cover" />
              : <img src="/placeholder.svg" alt="" className="w-full h-full object-cover" />
            }
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate">{listing.title || '—'}</p>
            <p className="text-xs text-base-content/60 truncate">{listing.address || '—'}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {listing.disposition && (
              <span className="badge badge-secondary badge-sm">{listing.disposition}</span>
            )}
            {listing.area_m2 && (
              <span className="badge badge-accent badge-sm hidden sm:inline-flex">{listing.area_m2} m²</span>
            )}
          </div>
          <div className="text-right flex-shrink-0 w-32">
            <p className="font-extrabold text-sm">{formatPrice(listing.price)}</p>
            <p className="text-[10px] text-base-content/40 font-mono">{listing.source}</p>
          </div>
          <div className="flex flex-col items-end gap-1 flex-shrink-0">
            {!listing.is_active && <span className="badge badge-error badge-xs">Neaktivní</span>}
            {listing.is_favorite && <span className="text-warning text-xs">★</span>}
            <p className="text-[10px] text-base-content/40 font-mono">
              {new Date(listing.first_seen_at).toLocaleDateString('cs-CZ')}
            </p>
          </div>
        </div>
      </Link>
    )
  }

  if (variant === 'mini') {
    return (
      <Link href={`/listing/${listing.id}`} className="block group">
        <div className="card bg-base-100 shadow hover:shadow-md transition-shadow overflow-hidden h-full">
          <figure className="relative aspect-video overflow-hidden bg-base-200">
            {img
              ? <img src={img} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
              : <img src="/placeholder.svg" alt="" className="w-full h-full object-cover" />
            }
            <div className="absolute top-1 left-1 flex gap-0.5">
              {!listing.is_active && <span className="badge badge-error badge-xs">Neakt.</span>}
              {listing.price_type === 'rent' && <span className="badge badge-info badge-xs">Pron.</span>}
            </div>
            {listing.is_favorite && (
              <span className="absolute top-1 right-1 text-warning text-xs drop-shadow">★</span>
            )}
          </figure>
          <div className="p-2 gap-0.5 flex flex-col">
            <p className="font-semibold text-xs truncate leading-tight">{listing.title || '—'}</p>
            <p className="text-xs font-extrabold text-black">{formatPrice(listing.price)}</p>
            <div className="flex flex-wrap gap-0.5 mt-0.5">
              {listing.disposition && <span className="badge badge-secondary badge-xs">{listing.disposition}</span>}
              {listing.area_m2 && <span className="badge badge-accent badge-xs">{listing.area_m2} m²</span>}
            </div>
          </div>
        </div>
      </Link>
    )
  }

  // box (default)
  return (
    <Link href={`/listing/${listing.id}`} className="block group">
      <div className="card bg-base-100 shadow hover:shadow-lg transition-shadow overflow-hidden h-full">
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
