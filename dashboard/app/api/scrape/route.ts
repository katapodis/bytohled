import { NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { SessionData, sessionOptions } from '@/lib/session'

export async function POST() {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const token = process.env.GITHUB_TOKEN
  const repo = process.env.GITHUB_REPO

  if (!token || !repo) {
    return NextResponse.json({ error: 'GITHUB_TOKEN nebo GITHUB_REPO není nastaveno' }, { status: 500 })
  }

  const triggeredAt = new Date().toISOString()

  const res = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/scraper.yml/dispatches`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ref: 'main' }),
  })

  if (!res.ok) {
    const text = await res.text()
    return NextResponse.json({ error: `GitHub API chyba: ${res.status} ${text}` }, { status: 502 })
  }

  return NextResponse.json({ ok: true, triggeredAt })
}
