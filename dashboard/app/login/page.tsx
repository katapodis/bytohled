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
      <input
        name="username"
        type="text"
        placeholder="Uživatelské jméno"
        required
        className="border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <input
        name="password"
        type="password"
        placeholder="Heslo"
        required
        className="border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="bg-blue-600 text-white rounded-lg py-2 font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Přihlašování...' : 'Přihlásit se'}
      </button>
    </form>
  )
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm bg-white rounded-xl shadow p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">BytoHled</h1>
        <Suspense fallback={<div className="text-center text-gray-400 text-sm">Načítám...</div>}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  )
}
