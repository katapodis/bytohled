'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

function LoginForm() {
  const router = useRouter()
  const params = useSearchParams()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const form = new FormData(e.currentTarget)
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: form.get('username'),
        password: form.get('password'),
      }),
    })

    if (res.ok) {
      const next = params.get('next') || '/listings'
      router.push(next.startsWith('/') ? next : '/listings')
    } else {
      const data = await res.json()
      setError(data.error || 'Chyba přihlášení')
    }
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className="form-control">
        <div className="label"><span className="label-text">Uživatelské jméno</span></div>
        <input name="username" type="text" autoComplete="username" required className="input input-bordered w-full" />
      </label>
      <label className="form-control">
        <div className="label"><span className="label-text">Heslo</span></div>
        <input name="password" type="password" autoComplete="current-password" required className="input input-bordered w-full" />
      </label>
      {error && (
        <div className="alert alert-error text-sm py-2">{error}</div>
      )}
      <button type="submit" disabled={loading} className="btn btn-primary w-full">
        {loading ? <span className="loading loading-spinner loading-sm" /> : 'Přihlásit se'}
      </button>
    </form>
  )
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200 p-4">
      <div className="card w-full max-w-sm bg-base-100 shadow-xl">
        <div className="card-body gap-6">
          <div className="text-center">
            <img src="/logo-full.svg" alt="BytoHled" className="h-12 mx-auto mb-1" />
            <p className="text-base-content/60 text-sm mt-1">Přihlaste se pro přístup</p>
          </div>
          <Suspense fallback={<div className="flex justify-center py-4"><span className="loading loading-dots" /></div>}>
            <LoginForm />
          </Suspense>
        </div>
      </div>
    </div>
  )
}
