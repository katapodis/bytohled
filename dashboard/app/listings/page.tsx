import { Suspense } from 'react'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { getIronSession } from 'iron-session'
import { supabaseAdmin } from '@/lib/supabase'
import { SessionData, sessionOptions } from '@/lib/session'
import { getCitiesForKraj, getCitiesForOkres } from '@/lib/geo'
import { Listing } from '@/types/listing'
import ListingsView from '@/components/ListingsView'
import FilterBar from '@/components/FilterBar'
import LogoutButton from '@/components/LogoutButton'
import ScrapeButton from '@/components/ScrapeButton'
import ScrapeLogModal from '@/components/ScrapeLogModal'

interface Props {
  searchParams: Promise<Record<string, string>>
}

interface ScrapeSummary {
  lastScraped: string
  added: number
  deactivated: number
}

async function getScrapeSummary(): Promise<ScrapeSummary | null> {
  const { data: latest } = await supabaseAdmin
    .from('listings')
    .select('last_checked_at')
    .order('last_checked_at', { ascending: false })
    .limit(1)
    .single()

  if (!latest?.last_checked_at) return null

  const lastScraped = latest.last_checked_at
  const windowStart = new Date(new Date(lastScraped).getTime() - 35 * 60 * 1000).toISOString()

  const [{ count: added }, { count: deactivated }] = await Promise.all([
    supabaseAdmin
      .from('listings')
      .select('*', { count: 'exact', head: true })
      .gte('first_seen_at', windowStart),
    supabaseAdmin
      .from('listings')
      .select('*', { count: 'exact', head: true })
      .eq('is_active', false)
      .gte('last_checked_at', windowStart),
  ])

  return { lastScraped, added: added ?? 0, deactivated: deactivated ?? 0 }
}

async function getListings(params: Record<string, string>) {
  const page = Math.max(1, parseInt(params.page || '1'))
  const perPage = 50
  const from = (page - 1) * perPage
  const to = from + perPage - 1

  let query = supabaseAdmin.from('listings').select('*', { count: 'exact' })

  const sources = params.sources?.split(',').filter(Boolean) ?? []
  if (sources.length === 1) query = query.eq('source', sources[0])
  else if (sources.length > 1) query = query.in('source', sources)

  const dispositions = params.dispositions?.split(',').filter(Boolean) ?? []
  if (dispositions.length === 1) query = query.eq('disposition', dispositions[0])
  else if (dispositions.length > 1) query = query.in('disposition', dispositions)
  if (params.price_type) query = query.eq('price_type', params.price_type)
  if (params.min_price) query = query.gte('price', parseInt(params.min_price))
  if (params.max_price) query = query.lte('price', parseInt(params.max_price))

  if (params.city) {
    query = query.eq('city', params.city)
  } else if (params.okres && params.kraj) {
    const cities = getCitiesForOkres(params.kraj, params.okres)
    if (cities.length > 0) query = query.in('city', cities)
  } else if (params.kraj) {
    const cities = getCitiesForKraj(params.kraj)
    if (cities.length > 0) query = query.in('city', cities)
  }

  if (params.only_active === '1') query = query.eq('is_active', true)
  if (params.only_favorites === '1') query = query.eq('is_favorite', true)

  const sortOptions: Record<string, { col: string; ascending: boolean }> = {
    date_asc:        { col: 'first_seen_at', ascending: true },
    price_asc:       { col: 'price',         ascending: true },
    price_desc:      { col: 'price',         ascending: false },
    disposition_asc: { col: 'disposition',   ascending: true },
    disposition_desc:{ col: 'disposition',   ascending: false },
    city_asc:        { col: 'city',          ascending: true },
    city_desc:       { col: 'city',          ascending: false },
  }
  const { col: sortCol, ascending } = sortOptions[params.sort ?? ''] ?? { col: 'first_seen_at', ascending: false }

  return query
    .order(sortCol, { ascending, nullsFirst: false })
    .range(from, to)
}

export default async function ListingsPage({ searchParams }: Props) {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) redirect('/login')

  const params = await searchParams
  const page = Math.max(1, parseInt(params.page || '1'))
  const [{ data, count }, scrapeSummary] = await Promise.all([
    getListings(params),
    getScrapeSummary(),
  ])
  const listings = (data || []) as Listing[]
  const totalPages = Math.ceil((count || 0) / 50)

  return (
    <div className="min-h-screen bg-base-200 p-5">
      <div className="max-w-7xl mx-auto">
        {/* Hlavička */}
        <div className="card bg-base-100 shadow-sm mb-2">
          <div className="card-body p-3 flex flex-row items-center gap-3">

            {/* Brand */}
            <img src="/logo-full.svg" alt="BytoHled" className="h-8 flex-shrink-0" />
            <span className="badge badge-neutral badge-sm">{count ?? 0} inzerátů</span>

            <div className="flex-1" />

            {/* Scrape summary */}
            {scrapeSummary && (
              <div className="hidden sm:flex items-center gap-2">
                <span className="text-[10px] text-base-content/35 uppercase tracking-widest">Scrape</span>
                <span className="font-mono text-xs text-base-content/55">
                  {new Date(scrapeSummary.lastScraped).toLocaleString('cs-CZ', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit',
                  })}
                </span>
                <span className="badge badge-success badge-sm gap-1 font-semibold">
                  +{scrapeSummary.added}
                </span>
                <span className="badge badge-error badge-sm gap-1 font-semibold">
                  ✕{scrapeSummary.deactivated}
                </span>
              </div>
            )}

            <div className="divider divider-horizontal mx-1 h-7" />

            {/* Scrape akce */}
            <div className="flex flex-col items-end gap-0.5">
              <ScrapeButton />
              <ScrapeLogModal />
            </div>

            <div className="divider divider-horizontal mx-1 h-7" />

            <LogoutButton />
          </div>
        </div>

        <Suspense>
          <FilterBar />
        </Suspense>

        {listings.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-base-content/40">
            <p className="text-4xl mb-3">🔍</p>
            <p className="text-sm">Žádné inzeráty nenalezeny.</p>
          </div>
        ) : (
          <ListingsView listings={listings} />
        )}

        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-2 mt-8">
            {page > 1 ? (
              <a
                href={`/listings?${new URLSearchParams({ ...params, page: String(page - 1) })}`}
                className="btn btn-sm btn-outline"
              >← Předchozí</a>
            ) : <div className="w-[95px]" />}
            <span className="text-sm text-base-content/50 tabular-nums">{page} / {totalPages}</span>
            {page < totalPages ? (
              <a
                href={`/listings?${new URLSearchParams({ ...params, page: String(page + 1) })}`}
                className="btn btn-sm btn-outline"
              >Další →</a>
            ) : <div className="w-[67px]" />}
          </div>
        )}
      </div>
    </div>
  )
}
