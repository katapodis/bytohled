import { NextRequest, NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { SessionData, sessionOptions } from '@/lib/session'
import { supabaseAdmin } from '@/lib/supabase'
import { getCitiesForKraj, getCitiesForOkres } from '@/lib/geo'

export async function GET(req: NextRequest) {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { searchParams } = req.nextUrl
  const page = Math.max(1, parseInt(searchParams.get('page') || '1'))
  const perPage = 50
  const from = (page - 1) * perPage
  const to = from + perPage - 1

  let query = supabaseAdmin.from('listings').select('*', { count: 'exact' })

  const sources = (searchParams.get('sources') || '').split(',').filter(Boolean)
  if (sources.length === 1) query = query.eq('source', sources[0])
  else if (sources.length > 1) query = query.in('source', sources)

  const dispositions = (searchParams.get('dispositions') || '').split(',').filter(Boolean)
  if (dispositions.length === 1) query = query.eq('disposition', dispositions[0])
  else if (dispositions.length > 1) query = query.in('disposition', dispositions)

  const priceType = searchParams.get('price_type')
  if (priceType) query = query.eq('price_type', priceType)

  const minPrice = searchParams.get('min_price')
  if (minPrice) query = query.gte('price', parseInt(minPrice))

  const maxPrice = searchParams.get('max_price')
  if (maxPrice) query = query.lte('price', parseInt(maxPrice))

  const city = searchParams.get('city')
  const okres = searchParams.get('okres')
  const kraj = searchParams.get('kraj')
  if (city) {
    query = query.eq('city', city)
  } else if (okres && kraj) {
    const cities = getCitiesForOkres(kraj, okres)
    if (cities.length > 0) query = query.in('city', cities)
  } else if (kraj) {
    const cities = getCitiesForKraj(kraj)
    if (cities.length > 0) query = query.in('city', cities)
  }

  if (searchParams.get('only_active') === '1') query = query.eq('is_active', true)
  if (searchParams.get('only_favorites') === '1') query = query.eq('is_favorite', true)

  const sortOptions: Record<string, { col: string; ascending: boolean }> = {
    date_asc:        { col: 'first_seen_at', ascending: true },
    price_asc:       { col: 'price',         ascending: true },
    price_desc:      { col: 'price',         ascending: false },
    disposition_asc: { col: 'disposition',   ascending: true },
    disposition_desc:{ col: 'disposition',   ascending: false },
    city_asc:        { col: 'city',          ascending: true },
    city_desc:       { col: 'city',          ascending: false },
  }
  const { col: sortCol, ascending } = sortOptions[searchParams.get('sort') ?? ''] ?? { col: 'first_seen_at', ascending: false }

  const { data, error, count } = await query
    .order(sortCol, { ascending, nullsFirst: false })
    .range(from, to)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  return NextResponse.json({ data, count, page, perPage })
}
