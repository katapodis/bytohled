import { NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { SessionData, sessionOptions } from '@/lib/session'
import { supabaseAdmin } from '@/lib/supabase'

export async function GET() {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { data, error } = await supabaseAdmin
    .from('listings')
    .select('city')
    .not('city', 'is', null)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  const cities = [...new Set((data ?? []).map((r) => r.city as string))].sort()
  return NextResponse.json(cities)
}
