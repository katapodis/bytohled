import { Suspense } from 'react'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { getIronSession } from 'iron-session'
import { supabaseAdmin } from '@/lib/supabase'
import { SessionData, sessionOptions } from '@/lib/session'
import { Listing } from '@/types/listing'
import ListingCard from '@/components/ListingCard'
import FilterBar from '@/components/FilterBar'
import LogoutButton from '@/components/LogoutButton'

interface Props {
  searchParams: Promise<Record<string, string>>
}

async function getListings(params: Record<string, string>) {
  const page = Math.max(1, parseInt(params.page || '1'))
  const perPage = 50
  const from = (page - 1) * perPage
  const to = from + perPage - 1

  let query = supabaseAdmin.from('listings').select('*', { count: 'exact' })

  if (params.source) query = query.eq('source', params.source)
  if (params.disposition) query = query.eq('disposition', params.disposition)
  if (params.price_type) query = query.eq('price_type', params.price_type)
  if (params.max_price) query = query.lte('price', parseInt(params.max_price))
  if (params.only_active === '1') query = query.eq('is_active', true)
  if (params.only_favorites === '1') query = query.eq('is_favorite', true)

  return query.order('first_seen_at', { ascending: false }).range(from, to)
}

export default async function ListingsPage({ searchParams }: Props) {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) redirect('/login')

  const params = await searchParams
  const page = Math.max(1, parseInt(params.page || '1'))
  const { data, count } = await getListings(params)
  const listings = (data || []) as Listing[]
  const totalPages = Math.ceil((count || 0) / 50)

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">BytoHled <span className="text-gray-400 text-lg font-normal">({count || 0} inzerátů)</span></h1>
          <LogoutButton />
        </div>

        <Suspense>
          <FilterBar />
        </Suspense>

        {listings.length === 0 ? (
          <p className="text-center text-gray-500 mt-12">Žádné inzeráty nenalezeny.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {listings.map((l) => <ListingCard key={l.id} listing={l} />)}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            {page > 1 && (
              <a href={`/listings?${new URLSearchParams({ ...params, page: String(page - 1) })}`}
                className="px-4 py-2 bg-white rounded-lg shadow text-sm hover:bg-gray-50">← Předchozí</a>
            )}
            <span className="px-4 py-2 text-sm text-gray-500">{page} / {totalPages}</span>
            {page < totalPages && (
              <a href={`/listings?${new URLSearchParams({ ...params, page: String(page + 1) })}`}
                className="px-4 py-2 bg-white rounded-lg shadow text-sm hover:bg-gray-50">Další →</a>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
