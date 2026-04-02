import { NextRequest, NextResponse } from 'next/server'
import { getIronSession } from 'iron-session'
import { cookies } from 'next/headers'
import { SessionData, sessionOptions } from '@/lib/session'

export async function GET(req: NextRequest) {
  const session = await getIronSession<SessionData>(await cookies(), sessionOptions)
  if (!session.isLoggedIn) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const token = process.env.GITHUB_TOKEN
  const repo = process.env.GITHUB_REPO
  if (!token || !repo) return NextResponse.json({ error: 'Chybí env' }, { status: 500 })

  const since = req.nextUrl.searchParams.get('since') ?? ''

  const res = await fetch(
    `https://api.github.com/repos/${repo}/actions/runs?event=workflow_dispatch&branch=main&per_page=5`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
      cache: 'no-store',
    }
  )

  if (!res.ok) return NextResponse.json({ status: 'unknown' })

  const json = await res.json()
  const runs: Array<{ created_at: string; status: string; conclusion: string | null }> =
    json.workflow_runs ?? []

  // Najdi první run vytvořený po triggeru
  const run = runs.find((r) => !since || r.created_at >= since)

  if (!run) return NextResponse.json({ status: 'queued' })

  // Mapuj GitHub stavy na naše
  if (run.status === 'completed') {
    return NextResponse.json({
      status: run.conclusion === 'success' ? 'completed' : 'failed',
    })
  }

  return NextResponse.json({ status: run.status }) // queued | in_progress | waiting
}
