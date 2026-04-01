import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMe, login, register } from '../api'
import { AppHeader } from '../components/AppHeader'
import { getSavedUser, getToken, saveToken, saveUser } from '../storage'

export function AuthPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('register')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '' })

  useEffect(() => {
    if (getToken() && getSavedUser()) {
      navigate('/events', { replace: true })
    }
  }, [navigate])

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const tokenResponse =
        mode === 'register'
          ? await register({ ...form, role: 'organizer' })
          : await login({ email: form.email, password: form.password })

      saveToken(tokenResponse.access_token)
      const me = await getMe(tokenResponse.access_token)
      saveUser(me)
      navigate(me.region ? '/events' : '/onboarding', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка авторизации')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen">
      <section className="party-board min-h-screen">
        <AppHeader />

        <div className="board-content mx-auto grid w-full max-w-6xl gap-8 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_0.95fr] lg:items-center lg:px-8">
          <section className="app-card p-6 sm:p-8">
            <div>
              <div>
                <div className='flex justify-between'>
                  <div className="text-sm uppercase tracking-[0.2em] text-white/65">{mode === 'register' ? 'Регистрация' : 'Вход'}</div>
                  <button type="button" className="text-sm font-semibold text-brand-orange" onClick={() => setMode((prev) => (prev === 'register' ? 'login' : 'register'))}>
                    {mode === 'register' ? 'Уже есть аккаунт?' : 'Нужен новый аккаунт?'}
                  </button>
                </div>
                <h2 className="mt-2 text-3xl font-bold text-white">{mode === 'register' ? 'Создать аккаунт' : 'Рады видеть снова'}</h2>
              </div>
            </div>

            {error ? <div className="mt-5 rounded-[18px] bg-red-500/15 px-4 py-3 text-sm text-red-100">{error}</div> : null}

            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              {mode === 'register' ? (
                <label className="block">
                  <span className="mb-2 block text-sm text-white/75">Имя</span>
                  <input className="field" value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Например, Алина" required />
                </label>
              ) : null}
              <label className="block">
                <span className="mb-2 block text-sm text-white/75">Email</span>
                <input className="field" type="email" value={form.email} onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))} placeholder="name@example.com" required />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-white/75">Пароль</span>
                <input className="field" type="password" value={form.password} onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))} placeholder="Минимум 6 символов" required />
              </label>
              <button className="primary-btn mt-2 w-full justify-center px-6 py-4 text-base" type="submit" disabled={loading}>
                {loading ? 'Подождите...' : mode === 'register' ? 'Создать аккаунт' : 'Войти'}
              </button>
            </form>
          </section>
        </div>
      </section>
    </main>
  )
}
