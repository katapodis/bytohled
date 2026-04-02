import { NextRequest, NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { supabaseAdmin } from '@/lib/supabase'
import { SessionData, sessionOptions } from '@/lib/session'

export async function GET(req: NextRequest) {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { searchParams } = req.nextUrl
  const page = Math.max(1, parseInt(searchParams.get('page') || '1'))
  const perPage = 20
  const from = (page - 1) * perPage
  const to = from + perPage - 1

  const dateFrom = searchParams.get('date_from')
  const dateTo = searchParams.get('date_to')

  let query = supabaseAdmin
    .from('scrape_logs')
    .select('*', { count: 'exact' })
    .order('scraped_at', { ascending: false })

  if (dateFrom) query = query.gte('scraped_at', dateFrom)
  if (dateTo) query = query.lte('scraped_at', dateTo + 'T23:59:59Z')

  const { data, count, error } = await query.range(from, to)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  return NextResponse.json({ data, count, page, perPage })
}
