import { NextRequest, NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { SessionData, sessionOptions } from '@/lib/session'
import { supabaseAdmin } from '@/lib/supabase'

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

  const source = searchParams.get('source')
  if (source) query = query.eq('source', source)

  const disposition = searchParams.get('disposition')
  if (disposition) query = query.eq('disposition', disposition)

  const priceType = searchParams.get('price_type')
  if (priceType) query = query.eq('price_type', priceType)

  const maxPrice = searchParams.get('max_price')
  if (maxPrice) query = query.lte('price', parseInt(maxPrice))

  const city = searchParams.get('city')
  if (city) query = query.eq('city', city)

  if (searchParams.get('only_active') === '1') query = query.eq('is_active', true)
  if (searchParams.get('only_favorites') === '1') query = query.eq('is_favorite', true)

  const { data, error, count } = await query
    .order('first_seen_at', { ascending: false })
    .range(from, to)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  return NextResponse.json({ data, count, page, perPage })
}
