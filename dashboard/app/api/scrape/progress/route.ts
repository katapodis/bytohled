import { NextRequest, NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { supabaseAdmin } from '@/lib/supabase'
import { SessionData, sessionOptions } from '@/lib/session'

export async function GET(req: NextRequest) {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const since = req.nextUrl.searchParams.get('since')
  if (!since) return NextResponse.json({ error: 'Chybí since' }, { status: 400 })

  const [{ data: added, count: addedCount }, { count: deactivatedCount }] = await Promise.all([
    supabaseAdmin
      .from('listings')
      .select('id,title,price,disposition,area_m2,address,images,source', { count: 'exact' })
      .gte('first_seen_at', since)
      .order('first_seen_at', { ascending: false })
      .limit(6),
    supabaseAdmin
      .from('listings')
      .select('*', { count: 'exact', head: true })
      .eq('is_active', false)
      .gte('last_checked_at', since),
  ])

  return NextResponse.json({
    addedCount: addedCount ?? 0,
    deactivatedCount: deactivatedCount ?? 0,
    recentListings: added ?? [],
  })
}
