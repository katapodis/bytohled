import { NextRequest, NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { SessionData, sessionOptions } from '@/lib/session'

export async function POST(req: NextRequest) {
  const { username, password } = await req.json()

  if (
    username !== process.env.DASHBOARD_USER ||
    password !== process.env.DASHBOARD_PASSWORD
  ) {
    return NextResponse.json({ error: 'Nesprávné přihlašovací údaje' }, { status: 401 })
  }

  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  session.isLoggedIn = true
  await session.save()
  return NextResponse.json({ ok: true })
}
