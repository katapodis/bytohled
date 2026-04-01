'use client'

export default function LogoutButton() {
  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    window.location.href = '/login'
  }

  return (
    <button onClick={handleLogout} className="btn btn-ghost btn-sm text-base-content/60">
      Odhlásit se
    </button>
  )
}
