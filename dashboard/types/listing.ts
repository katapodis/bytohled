export type PriceType = 'sale' | 'rent'

export interface Listing {
  id: string
  external_id: string
  source: string
  url: string
  title: string | null
  price: number | null
  price_type: PriceType
  disposition: string | null
  area_m2: number | null
  address: string | null
  description: string | null
  images: string[]
  is_active: boolean
  first_seen_at: string
  last_checked_at: string
  notified_at: string | null
  is_favorite: boolean
  note: string | null
}

export interface ListingsFilter {
  source?: string
  disposition?: string
  price_type?: PriceType
  max_price?: number
  only_active?: boolean
  only_favorites?: boolean
  page?: number
}
